from mcp.server.fastmcp import Context, FastMCP
from mcp.types import SamplingMessage, TextContent
from pydantic import Field
from mcp.server.fastmcp.prompts import base
import asyncio

# Create MCP server
mcp = FastMCP("mcp-server", stateless_http=False)

# Fake documents
docs = {
    "deposition.md": "Testimony of Angela Smith, P.E.",
    "report.pdf": "State of a 20m condenser tower.",
    "financials.docx": "Project budget and expenditures.",
    "outlook.pdf": "Future performance of the system.",
    "plan.md": "Steps for project implementation.",
    "spec.txt": "Technical requirements for the equipment.",
}

# TOOLS


@mcp.tool(name="doc_read_fixed", description="Read a fixed sample document.")
def doc_read_fixed() -> str:
    return docs["deposition.md"]


@mcp.tool(name="doc_read", description="Read any document by id.")
def doc_read(doc_id: str = Field(description="Document id")) -> str:
    if doc_id not in docs:
        raise ValueError("Document not found")
    return docs[doc_id]


# RESOURCES
@mcp.resource("docs://all", mime_type="application/json")
def docs_all() -> list[str]:
    return list(docs.keys())


@mcp.resource("docs://{doc_id}", mime_type="text/plain")
def docs_one(doc_id: str) -> str:
    return docs[doc_id]


# PROMPTS
@mcp.prompt(name="doc_list", description="Shows available documents.")
def doc_list() -> list[base.Message]:
    return [base.UserMessage("\n".join(docs.keys()))]


@mcp.prompt(name="doc_format", description="Ask to format a document to markdown.")
def doc_format(doc_id: str = Field(description="Document id")) -> list[base.Message]:
    msg = f"Reformat document <document_id>{doc_id}</document_id> into markdown."
    return [base.UserMessage(msg)]


# SAMPLING + LOGGING + PROGRESS
@mcp.tool(
    name="doc_summarize",
    description="Generate a short summary of a document via client sampling, with logging and progress.",
)
async def doc_summarize(ctx: Context, doc_id: str = Field(description="Document id")) -> str:
    if doc_id not in docs:
        await ctx.error(f"Document '{doc_id}' not found")
        return f"Error: Document '{doc_id}' not found."

    await ctx.info(f"Starting summarization for '{doc_id}'")
    await ctx.log("info", {"progress": 10, "message": "Preparing request for client sampling..."})
    await asyncio.sleep(0.3)

    try:
        result = await ctx.session.create_message(
            messages=[
                SamplingMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=(
                            "Please write a very short summary (2-3 sentences) of the following document:\n"
                            f"{docs[doc_id]}"
                        ),
                    ),
                )
            ],
            max_tokens=150,
        )

        await ctx.log("info", {"progress": 70, "message": "Client sampling completed, processing response..."})
        await asyncio.sleep(0.2)

        if result.content.type == "text":
            summary = result.content.text
            await ctx.info(f"Summarization for '{doc_id}' completed successfully")
            await ctx.log("info", {"progress": 100, "message": "Done"})
            return summary

        await ctx.warning(f"Unexpected content type from client: {result.content.type}")
        return str(result.content)

    except Exception as e:
        await ctx.error(f"Summarization failed: {e}")
        return f"Error generating summary via client sampling: {e}"


# Run app
mcp_app = mcp.streamable_http_app()

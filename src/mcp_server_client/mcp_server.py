from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp.server.fastmcp.prompts import base

# Create MCP server
mcp = FastMCP("mcp-server", stateless_http=True)

# Our fake documents
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



# Run app
mcp_app = mcp.streamable_http_app()

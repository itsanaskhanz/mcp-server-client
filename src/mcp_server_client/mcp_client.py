import os
from dotenv import load_dotenv
import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, types
from mcp.client.streamable_http import streamablehttp_client
load_dotenv()


class MCPClient:
    def __init__(self, server_url: str):
        self._server_url = server_url
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        streamable_transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(self._server_url)
        )
        _read, _write, _get_session_id = streamable_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_read, _write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized. Call connect first."
            )
        return self._session

    async def list_tools(self) -> types.ListToolsResult:
        result = await self.session().list_tools()
        return result

    async def call_tool(self, tool_name: str, tool_input: dict) -> types.CallToolResult:
        return await self.session().call_tool(tool_name, tool_input)

    async def list_resource(self):
        result = await self.session().list_resources()
        return result

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(uri)
        return result

    async def list_template_resource(self) -> Any:
        return await self.session().list_resource_templates()

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


async def main():
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    async with MCPClient(mcp_server_url) as client:
        # TOOLS
        tools = await client.list_tools()
        # print("Tools:", tools)
        if tools:
            # Call static tool
            static_result = await client.call_tool("doc_read_fixed", {})
            print("Static tool result:", static_result)
            # Call dynamic tool
            dynamic_result = await client.call_tool("doc_read", {"doc_id": "plan.md"})
            print("Dynamic tool result:", dynamic_result)

       # LIST RESOURCES
        resources = await client.list_resource()
        print("All resources:", resources)

        static_resource = await client.read_resource("docs://all")
        print("Static resource (all docs):", static_resource)

        # DYNAMIC RESOURCE
        resource_templates = await client.list_template_resource()
        print("Resource templates:", resource_templates)
        if resource_templates.resourceTemplates:
            template_uri = resource_templates.resourceTemplates[0].uriTemplate
            doc_uri = template_uri.replace(
                "{doc_id}", "plan.md")  # replace with desired doc
            dynamic_resource = await client.read_resource(doc_uri)
            print("Dynamic resource (plan.md):", dynamic_resource)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())

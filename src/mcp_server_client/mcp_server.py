from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mcp-server", stateless_http=True)



mcp_app = mcp.streamable_http_app()

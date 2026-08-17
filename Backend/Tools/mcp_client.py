import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def mcp_func():
    client = MultiServerMCPClient(
        {
            "demo": {
                "transport": "stdio",
                "command": "python",
                "args": [r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Mcp_Server\mcp_server.py"]
            }
        }
    )

    tools = await client.get_tools()
    print("Tools from mcp_clinet.py:", tools)
    return tools



# asyncio.run(mcp_func())
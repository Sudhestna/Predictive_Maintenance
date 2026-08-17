from mcp.server.fastmcp import FastMCP
import requests
import json
mcp = FastMCP("Demo Server")
from typing import Optional

@mcp.tool()
def get_sensor_data(m_id:str):
    """Returns sensor live data"""
    if m_id:
        response = requests.get(
            f"http://localhost:5000/live-sensors/{m_id}",
            timeout=10)

        return json.dumps(response.json())
    return "Please provide valid machine ID"

if __name__ == "__main__":
    mcp.run(transport="stdio")


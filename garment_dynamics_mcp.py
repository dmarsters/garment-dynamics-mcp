from fastmcp import FastMCP

mcp = FastMCP("garment-dynamics")

from layers.taxonomy import register_taxonomy_tools
from layers.computation import register_computation_tools
from layers.synthesis import register_synthesis_tools

register_taxonomy_tools(mcp)
register_computation_tools(mcp)
register_synthesis_tools(mcp)

if __name__ == "__main__":
    mcp.run()

import os
import sys
import asyncio
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, 
    CallToolResult, 
    TextContent,
)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

WORKSPACE = os.path.expanduser("/Users/lucaboerio/vs_code/assignment2/file_workspace")
os.makedirs(WORKSPACE, exist_ok=True)

server = Server("file-agent")

"""
def safe_path(filename: str) -> str:
    basename = os.path.basename(filename)
    return os.path.join(WORKSPACE, basename)
"""

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    return [
        Tool(
            name="list_files",
            description="List all files in workspace",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"]
            }
        ),
        Tool(
            name="delete_file",
            description="Delete a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> List[TextContent]:
    logger.info(f"Tool called: {name}")
    
    try:
        if name == "list_files":
            files = os.listdir(WORKSPACE)
            if not files:
                text = "No files in workspace"
            else:
                file_list = []
                for f in files:
                    size = os.path.getsize(os.path.join(WORKSPACE, f))
                    file_list.append(f"- {f} ({size} bytes)")
                text = "Files in workspace:\n" + "\n".join(file_list)
        
        elif name == "read_file":
            filename = arguments.get("filename", "")
            path = os.path.join(WORKSPACE, filename)
            
            if not os.path.exists(path):
                text = f"Error: File '{filename}' not found"
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                text = f"Content of '{filename}':\n{content}"
        
        elif name == "write_file":
            filename = arguments.get("filename", "")
            content = arguments.get("content", "")
            path = os.path.join(WORKSPACE, filename)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            text = f"Successfully wrote to '{filename}'"
        
        elif name == "delete_file":
            filename = arguments.get("filename", "")
            path = os.path.join(WORKSPACE, filename)
            
            if os.path.exists(path):
                os.remove(path)
                text = f"Successfully deleted '{filename}'"
            else:
                text = f"Error: File '{filename}' not found"
        
        else:
            text = f"Error: Unknown tool '{name}'"
        
        return [TextContent(type="text", text=text)]
    
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    logger.info("Starting MCP server...")
    logger.info(f"Workspace: {WORKSPACE}")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
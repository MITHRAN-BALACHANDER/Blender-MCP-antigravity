"""
Antigravity MCP Server for Blender

This MCP server provides the `blender_exec` tool that sends Python scripts
to a running Blender instance and returns the results.

Usage:
    python antigravity_blender_server.py
"""

import socket
import json
import logging
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("blender-mcp")

# Configuration
BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 8081
TIMEOUT = 120  # 2 minute timeout for script execution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def send_to_blender(script: str) -> dict:
    """
    Send a script to Blender and collect all responses.
    
    Returns a dict with:
    - status: 'ok', 'error', or 'timeout'
    - messages: list of all status messages received
    - error: error message if status is 'error'
    - trace: stack trace if available
    """
    results = {
        "status": "unknown",
        "messages": [],
        "error": None,
        "trace": None
    }
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((BLENDER_HOST, BLENDER_PORT))
        
        # Send the script
        payload = json.dumps({"script": script})
        s.sendall(payload.encode())
        
        # Collect all responses (Blender sends multiple JSON lines)
        buffer = ""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode()
                
                # Process complete lines
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            
                            if msg.get("status") == "progress":
                                results["messages"].append(msg.get("message", ""))
                            elif msg.get("status") == "running":
                                results["messages"].append("Execution started")
                            elif msg.get("status") == "ok":
                                results["status"] = "ok"
                                results["messages"].append(msg.get("message", "Complete"))
                            elif msg.get("status") == "error":
                                results["status"] = "error"
                                results["error"] = msg.get("error", "Unknown error")
                                results["trace"] = msg.get("trace")
                        except json.JSONDecodeError:
                            pass
                
                # If we got a final status, we're done
                if results["status"] in ("ok", "error"):
                    break
                    
            except socket.timeout:
                results["status"] = "timeout"
                results["error"] = "Blender did not respond within timeout"
                break
        
        s.close()
        
    except ConnectionRefusedError:
        results["status"] = "error"
        results["error"] = "Could not connect to Blender. Is it running with blender_server.py?"
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
    
    return results


@mcp.tool()
def blender_exec(script: str) -> str:
    """
    Execute a Python script inside Blender.
    
    IMPORTANT RULES:
    - The script MUST define a main() function and call it
    - Use send_status("message") to report progress
    - Use bpy.data.* APIs instead of bpy.ops.* when possible
    - Script MUST terminate - no infinite loops
    - Catch exceptions and handle errors gracefully
    
    Args:
        script: Python code to execute in Blender. Has access to 'bpy' and 'send_status()'.
    
    Returns:
        JSON string with execution results including status and any messages.
    """
    result = send_to_blender(script)
    return json.dumps(result, indent=2)


@mcp.tool()
def get_blender_scene() -> str:
    """
    Get information about the current Blender scene.
    
    Returns:
        JSON string with lists of objects, meshes, materials, and collections.
    """
    script = '''
import bpy
import json

def main():
    send_status("Gathering scene data")
    
    data = {
        "objects": [{"name": o.name, "type": o.type} for o in bpy.data.objects],
        "meshes": [m.name for m in bpy.data.meshes],
        "materials": [m.name for m in bpy.data.materials],
        "collections": [c.name for c in bpy.data.collections],
    }
    
    # Store result for retrieval
    bpy.context.scene["_mcp_result"] = json.dumps(data)
    send_status("Scene data collected")

main()
'''
    result = send_to_blender(script)
    
    if result["status"] == "ok":
        # Try to get the stored result
        try:
            import bpy
            return bpy.context.scene.get("_mcp_result", "{}")
        except:
            return json.dumps({"status": "ok", "message": "Scene data collected"})
    
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    print("Starting Blender MCP Server...")
    print("Make sure Blender is running with: blender --background --python blender_server.py")
    mcp.run()

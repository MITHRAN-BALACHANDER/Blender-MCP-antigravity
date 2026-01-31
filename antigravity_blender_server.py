"""
Antigravity MCP Server for Blender

This MCP server provides tools for AI clients to control Blender:
- blender_exec: Execute Python scripts in Blender
- get_blender_scene: Get scene information
- image_to_3d_model: Create 3D models from images with matching colors

Usage:
    python antigravity_blender_server.py
"""

import socket
import json
import logging
import base64
import io
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


def extract_dominant_colors(image_data: str, num_colors: int = 5) -> list:
    """
    Extract dominant colors from a base64-encoded image.
    
    Returns a list of hex color strings.
    """
    try:
        from PIL import Image
        from collections import Counter
        
        # Decode base64 image
        if "," in image_data:
            # Handle data URL format
            image_data = image_data.split(",", 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Resize for faster processing
        image = image.resize((100, 100))
        
        # Get all pixels
        pixels = list(image.getdata())
        
        # Quantize colors to reduce variation
        def quantize_color(rgb, levels=8):
            factor = 256 // levels
            return tuple((c // factor) * factor + factor // 2 for c in rgb)
        
        quantized = [quantize_color(p) for p in pixels]
        
        # Count color occurrences
        color_counts = Counter(quantized)
        
        # Get most common colors
        top_colors = color_counts.most_common(num_colors)
        
        # Convert to hex
        hex_colors = []
        for color, _ in top_colors:
            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
            hex_colors.append(hex_color)
        
        return hex_colors
        
    except Exception as e:
        logger.error(f"Error extracting colors: {e}")
        # Return default colors if extraction fails
        return ["#FF5733", "#33FF57", "#3357FF", "#FFFF33", "#FF33FF"]


def generate_3d_model_script(colors: list, model_type: str = "cube", model_name: str = "ImageModel") -> str:
    """
    Generate a Blender Python script to create a 3D model with the given colors.
    """
    colors_json = json.dumps(colors)
    
    script = f'''
import bpy
import math
import json

def main():
    send_status("Starting 3D model creation from image colors...")
    
    # Clear existing model with same name
    if "{model_name}" in bpy.data.objects:
        obj = bpy.data.objects["{model_name}"]
        bpy.data.objects.remove(obj, do_unlink=True)
    
    colors = {colors_json}
    send_status(f"Extracted {{len(colors)}} colors: {{colors}}")
    
    # Create materials for each color
    materials = []
    for i, hex_color in enumerate(colors):
        mat_name = f"{model_name}_Mat_{{i}}"
        
        # Remove existing material
        if mat_name in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[mat_name])
        
        # Create new material
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        
        if bsdf:
            # Convert hex to RGB
            h = hex_color.lstrip('#')
            r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
            bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.5
        
        materials.append(mat)
    
    send_status("Materials created, building mesh...")
    
    # Create the mesh based on model type
    model_type = "{model_type}"
    
    if model_type == "sphere":
        # Create UV sphere using bmesh
        import bmesh
        mesh = bpy.data.meshes.new("{model_name}_mesh")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=2.0)
        bm.to_mesh(mesh)
        bm.free()
    elif model_type == "cylinder":
        # Create cylinder using bmesh
        import bmesh
        mesh = bpy.data.meshes.new("{model_name}_mesh")
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, segments=16, radius1=1.5, radius2=1.5, depth=3.0)
        bm.to_mesh(mesh)
        bm.free()
    else:
        # Create cube with subdivisions for more faces to color
        import bmesh
        mesh = bpy.data.meshes.new("{model_name}_mesh")
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=3.0)
        # Subdivide for more faces
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2)
        bm.to_mesh(mesh)
        bm.free()
    
    # Create object
    obj = bpy.data.objects.new("{model_name}", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Add all materials to object
    for mat in materials:
        obj.data.materials.append(mat)
    
    # Assign materials to faces based on color distribution
    if len(obj.data.polygons) > 0 and len(materials) > 0:
        for i, poly in enumerate(obj.data.polygons):
            # Distribute colors across faces
            mat_index = i % len(materials)
            poly.material_index = mat_index
    
    send_status(f"Created {model_type} with {{len(obj.data.polygons)}} faces")
    
    # Center the object
    obj.location = (0, 0, 0)
    
    # Make it the active object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    send_status(f"3D model '{model_name}' created successfully with {{len(colors)}} color materials!")

main()
'''
    return script


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


@mcp.tool()
def image_to_3d_model(image_data: str, model_type: str = "cube", model_name: str = "ImageModel") -> str:
    """
    Create a 3D model in Blender with colors extracted from an image.
    
    This tool analyzes the provided image to extract dominant colors, then creates
    a 3D model in Blender with materials matching those colors.
    
    Args:
        image_data: Base64-encoded image data (can include data URL prefix)
        model_type: Shape type - "cube", "sphere", or "cylinder" (default: "cube")
        model_name: Name for the created 3D object (default: "ImageModel")
    
    Returns:
        JSON string with status, extracted colors, and model information.
    """
    logger.info(f"Processing image for 3D model creation...")
    
    # Extract colors from image
    colors = extract_dominant_colors(image_data, num_colors=5)
    logger.info(f"Extracted colors: {colors}")
    
    # Generate Blender script
    script = generate_3d_model_script(colors, model_type, model_name)
    
    # Execute in Blender
    result = send_to_blender(script)
    
    # Add color info to result
    result["colors"] = colors
    result["object_name"] = model_name
    result["model_type"] = model_type
    
    return json.dumps(result, indent=2)


def main():
    """Entry point for the MCP server."""
    print("=" * 60)
    print("Blender MCP Server - Starting...")
    print("=" * 60)
    print()
    print("Available tools:")
    print("  • blender_exec      - Execute Python scripts in Blender")
    print("  • get_blender_scene - Get scene information")
    print("  • image_to_3d_model - Create 3D model from image colors")
    print()
    print("Make sure Blender is running with:")
    print("  blender --background --python blender_server.py")
    print()
    print("=" * 60)
    mcp.run()


if __name__ == "__main__":
    main()

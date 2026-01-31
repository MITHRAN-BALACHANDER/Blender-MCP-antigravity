# 🎨 Blender MCP Bridge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![Blender 2.80+](https://img.shields.io/badge/Blender-2.80+-orange.svg)](https://www.blender.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **AI-powered Blender control via Model Context Protocol (MCP)**
>
> Send images to create 3D models with matching colors, execute Python scripts, and control Blender remotely through Antigravity or any MCP-compatible AI client.

---

## ✨ Features

- 🖼️ **Image to 3D Model** - Send an image and get a 3D model with colors extracted from the image
- 🐍 **Execute Python Scripts** - Run any Blender Python code remotely
- 📊 **Scene Inspection** - Query objects, materials, and collections in the current scene
- ⚡ **Real-time Progress** - Get live status updates during script execution
- 🔒 **Thread-safe** - Robust multi-threaded architecture with guaranteed responses

---

## 🏗️ Architecture

```
┌─────────────────────┐       MCP/stdio       ┌─────────────────────────┐
│     Antigravity     │◄─────────────────────►│  antigravity_blender_   │
│   (or any MCP AI)   │                       │  server.py              │
└─────────────────────┘                       └───────────┬─────────────┘
                                                          │
                                                          │ TCP Socket
                                                          │ (port 8081)
                                                          ▼
                                              ┌─────────────────────────┐
                                              │   blender_server.py     │
                                              │  (runs inside Blender)  │
                                              └─────────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- **Python 3.10+**
- **Blender 2.80+** (installed and accessible via command line)

### Option 1: Install from PyPI (Recommended)

```bash
pip install blender-mcp
```

### Option 2: Install from Source

```bash
git clone https://github.com/antigravity/blender-mcp.git
cd blender-mcp
pip install -e .
```

### Option 3: Manual Installation

```bash
git clone https://github.com/antigravity/blender-mcp.git
cd blender-mcp
pip install -r requirements.txt
```

---

## 🔌 Antigravity Integration

Add the following configuration to your Antigravity MCP settings:

### Configuration JSON

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["path/to/antigravity_blender_server.py"],
      "env": {}
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "blender": {
      "command": "blender-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

### Steps to Configure

1. Open Antigravity settings
2. Navigate to **MCP Servers** configuration
3. Add the JSON configuration above
4. Replace `path/to/` with the actual path to your installation
5. Restart Antigravity to apply changes

---

## 🚀 Quick Start

### Step 1: Start the Blender Server

Open a terminal and run:

```bash
# Background mode (headless)
blender --background --python blender_server.py

# Interactive mode (with viewport)
blender --python blender_server.py
```

You should see:
```
==================================================
[BlenderMCP] Server running on 127.0.0.1:8081
[BlenderMCP] Waiting for connections...
==================================================
```

### Step 2: Connect via Antigravity

Once Blender is running with the server, Antigravity can connect and use the available tools.

### Step 3: Create Your First 3D Model

Simply send an image to Antigravity and ask it to create a 3D model from it:

> "Create a 3D model in Blender based on this image"

The AI will extract colors from your image and create a 3D model with matching materials!

---

## 🛠️ Available MCP Tools

### `image_to_3d_model`

Creates a 3D model in Blender with colors extracted from an image.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_data` | string | Yes | Base64-encoded image data |
| `model_type` | string | No | Shape type: "cube", "sphere", "cylinder" (default: "cube") |
| `model_name` | string | No | Name for the created object (default: "ImageModel") |

**Example Response:**
```json
{
  "status": "ok",
  "message": "Created 3D model with 5 color materials",
  "colors": ["#FF5733", "#33FF57", "#3357FF", "#FFFF33", "#FF33FF"],
  "object_name": "ImageModel"
}
```

---

### `blender_exec`

Execute arbitrary Python code inside Blender.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `script` | string | Yes | Python code to execute in Blender |

**Important Rules for Scripts:**
1. ✅ Define and call a `main()` function
2. ✅ Use `send_status("message")` for progress updates
3. ✅ Use `bpy.data.*` APIs instead of `bpy.ops.*`
4. ❌ No infinite loops
5. ❌ No UI dependencies

**Example Script:**
```python
import bpy

def main():
    send_status("Creating cube...")
    
    # Create mesh using bpy.data APIs
    mesh = bpy.data.meshes.new("MyCube")
    obj = bpy.data.objects.new("MyCube", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Create cube geometry
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(mesh)
    bm.free()
    
    send_status("Cube created!")

main()
```

**Response:**
```json
{
  "status": "ok",
  "messages": ["Creating cube...", "Cube created!"]
}
```

---

### `get_blender_scene`

Get information about the current Blender scene.

**Parameters:** None

**Response:**
```json
{
  "objects": [
    {"name": "Cube", "type": "MESH"},
    {"name": "Camera", "type": "CAMERA"},
    {"name": "Light", "type": "LIGHT"}
  ],
  "meshes": ["Cube"],
  "materials": ["Material"],
  "collections": ["Collection"]
}
```

---

## 📁 Project Structure

```
blender_mcp_bridge/
├── antigravity_blender_server.py  # MCP server (connects to AI clients)
├── blender_server.py              # Socket server (runs inside Blender)
├── antigravity_blender_addon.py   # Optional Blender UI addon
├── generate_island.py             # Example: procedural island scene
├── run_via_bridge.py              # Standalone script runner
├── requirements.txt               # Python dependencies
├── pyproject.toml                 # Package configuration
└── README.md                      # This file
```

---

## 🔧 Troubleshooting

### Connection Refused

**Problem:** Cannot connect to Blender

**Solution:**
1. Ensure Blender is running with the server:
   ```bash
   blender --background --python blender_server.py
   ```
2. Check if port 8081 is available
3. Verify firewall settings

### Timeout Error

**Problem:** Script execution times out

**Solution:**
1. Check Blender's console for errors
2. Ensure your script calls `main()` at the end
3. Avoid infinite loops or blocking operations
4. For long operations, add `send_status()` calls

### Port Already in Use

**Problem:** Address already in use error

**Solution:**
1. Kill existing Blender processes:
   ```bash
   # Windows
   taskkill /F /IM blender.exe
   
   # Linux/Mac
   pkill blender
   ```
2. Or change the port in both `blender_server.py` and `antigravity_blender_server.py`

### Nothing Appears in Blender

**Problem:** Script runs but no visible changes

**Solution:**
1. Open Blender's System Console: **Window → Toggle System Console**
2. Check for error messages
3. Ensure you're linking objects to a collection:
   ```python
   bpy.context.collection.objects.link(obj)
   ```

---

## 🎯 Examples

### Create a Low-Poly Island

```bash
python run_via_bridge.py generate_island.py
```

This creates a complete island scene with:
- 🏝️ Terrain mesh
- 🏠 House structure
- 🌳 Trees and rocks
- ⛵ Dock with boat
- 🌊 Water plane
- 💡 Lighting and camera

### Custom Script Execution

```python
from run_via_bridge import send_script

script = '''
import bpy

def main():
    send_status("Creating sphere...")
    mesh = bpy.data.meshes.new("Sphere")
    obj = bpy.data.objects.new("Sphere", mesh)
    bpy.context.collection.objects.link(obj)
    
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    bm.to_mesh(mesh)
    bm.free()
    
    send_status("Done!")

main()
'''

send_script(script)
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/antigravity/blender-mcp.git
cd blender-mcp
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -e .
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Blender](https://www.blender.org/) - The amazing open-source 3D creation suite
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol that makes AI tool integration possible
- [Antigravity](https://antigravity.dev/) - AI coding assistant

---

<p align="center">
  Made with ❤️ for the AI + 3D community
</p>

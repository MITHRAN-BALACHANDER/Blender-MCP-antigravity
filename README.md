# 🎨 Blender MCP Bridge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![Blender 4.2+](https://img.shields.io/badge/Blender-4.2+-orange.svg)](https://www.blender.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **AI-powered Blender control via Model Context Protocol (MCP)**
>
> Send images to create 3D models with matching colors, execute Python scripts, and control Blender remotely through Antigravity or any MCP-compatible AI client.

<p align="center">
  <img src="https://raw.githubusercontent.com/MITHRAN-BALACHANDER/Blender-MCP-antigravity/main/island_render.png" alt="Low-Poly Island Demo" width="600"/>
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Image to 3D** | Extract dominant colors from images and create 3D models with matching materials |
| 🐍 **Script Execution** | Run any Blender Python code remotely through MCP |
| 📊 **Scene Query** | Get detailed information about objects, materials, and collections |
| ⚡ **Real-time Updates** | Receive live progress status during script execution |
| 🔒 **Thread-safe** | Robust architecture with guaranteed responses and no deadlocks |

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
- **Blender 4.2+** (with full path accessible)
- **pip** (Python package manager)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/MITHRAN-BALACHANDER/Blender-MCP-antigravity.git
cd Blender-MCP-antigravity

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate      # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Install as Package (Optional)

```bash
pip install -e .
```

---

## 🔌 Antigravity Integration

Add the following to your Antigravity MCP server configuration:

### Option A: Direct Path

```json
{
  "mcpServers": {
    "blender": {
      "command": "python",
      "args": ["C:/path/to/Blender-MCP-antigravity/antigravity_blender_server.py"],
      "env": {}
    }
  }
}
```

### Option B: Using Virtual Environment

```json
{
  "mcpServers": {
    "blender": {
      "command": "C:/path/to/Blender-MCP-antigravity/venv/Scripts/python.exe",
      "args": ["C:/path/to/Blender-MCP-antigravity/antigravity_blender_server.py"],
      "env": {}
    }
  }
}
```

> **Note:** Replace `C:/path/to/` with your actual installation path.

---

## 🚀 Quick Start

### Step 1: Start Blender Server

```bash
# Navigate to project directory
cd Blender-MCP-antigravity

# Start Blender with the socket server
# Windows (use full path if 'blender' is not in PATH)
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python blender_server.py

# Linux/Mac
blender --background --python blender_server.py
```

Expected output:
```
==================================================
[BlenderMCP] Server running on 127.0.0.1:8081
[BlenderMCP] Waiting for connections...
==================================================
```

### Step 2: Connect Antigravity

Once Blender is running, Antigravity will automatically connect via the MCP configuration.

### Step 3: Create 3D Content

Ask Antigravity to create 3D content:

> "Create a low-poly island scene in Blender"

> "Create a 3D model from this image" (with attached image)

---

## 🛠️ MCP Tools Reference

### `image_to_3d_model`

Create a 3D model with colors extracted from an image.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_data` | string | ✅ | - | Base64-encoded image |
| `model_type` | string | ❌ | `"cube"` | Shape: `cube`, `sphere`, `cylinder` |
| `model_name` | string | ❌ | `"ImageModel"` | Name for the object |

**Response:**
```json
{
  "status": "ok",
  "colors": ["#3A7D8C", "#D4C4A0", "#4A6E4A"],
  "object_name": "ImageModel"
}
```

---

### `blender_exec`

Execute Python code inside Blender.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `script` | string | ✅ | Python code to execute |

**Script Requirements:**
- ✅ Define and call a `main()` function
- ✅ Use `send_status("message")` for progress updates
- ✅ Use `bpy.data.*` APIs (not `bpy.ops.*`)
- ❌ No infinite loops or blocking operations

**Example:**
```python
import bpy

def main():
    send_status("Creating cube...")
    mesh = bpy.data.meshes.new("Cube")
    obj = bpy.data.objects.new("Cube", mesh)
    bpy.context.collection.objects.link(obj)
    
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(mesh)
    bm.free()
    
    send_status("Done!")

main()
```

---

### `get_blender_scene`

Query the current Blender scene.

**Response:**
```json
{
  "objects": [
    {"name": "Cube", "type": "MESH"},
    {"name": "Camera", "type": "CAMERA"}
  ],
  "meshes": ["Cube"],
  "materials": ["Material"],
  "collections": ["Collection"]
}
```

---

## 📁 Project Structure

```
Blender-MCP-antigravity/
├── antigravity_blender_server.py   # MCP server (AI client interface)
├── blender_server.py               # TCP server (runs in Blender)
├── antigravity_blender_addon.py    # Blender UI addon (optional)
├── run_via_bridge.py               # Standalone script runner
├── generate_island.py              # Example: procedural island
├── create_island_from_image.py     # Example: island from reference
├── requirements.txt                # Dependencies
├── pyproject.toml                  # Package config
└── README.md
```

---

## 🔧 Troubleshooting

### Connection Refused

```bash
# Ensure Blender is running with the server
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --background --python blender_server.py

# Check if port 8081 is in use
netstat -an | findstr 8081   # Windows
lsof -i :8081                # Linux/Mac
```

### Timeout Errors

1. Check Blender's console for Python errors
2. Ensure `main()` is called at the end of your script
3. Add `send_status()` calls for long operations
4. Avoid blocking calls or infinite loops

### Port Already in Use

```bash
# Kill existing Blender processes
taskkill /F /IM blender.exe     # Windows
pkill blender                    # Linux/Mac
```

---

## 🎯 Examples

### Run the Island Generator

```bash
# Activate venv first
.\venv\Scripts\activate

# Run example script
python run_via_bridge.py generate_island.py
```

### Interactive Mode (View Output)

```bash
# Start Blender with GUI
"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe" --python blender_server.py

# Then run scripts via bridge
python run_via_bridge.py your_script.py
```

---

## 🤝 Contributing

Contributions are welcome! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🔗 Links

- **Repository:** [github.com/MITHRAN-BALACHANDER/Blender-MCP-antigravity](https://github.com/MITHRAN-BALACHANDER/Blender-MCP-antigravity)
- **Blender:** [blender.org](https://www.blender.org/)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io/)
- **Antigravity:** [antigravity.dev](https://antigravity.dev/)

---

<p align="center">
  Made with <a href="https://github.com/MITHRAN-BALACHANDER">Mithran Balachander</a>
</p>

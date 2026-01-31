# Blender MCP Verification & Usage Guide

## ✅ Checklist
- [x] Created `blender_mcp_bridge` directory
- [x] Created Virtual Environment (`venv`)
- [x] Installed dependencies (`mcp`)
- [x] Created MCP Server Script (`antigravity_blender_server.py`)
- [x] Created Blender Addon Script (`antigravity_blender_addon.py`) - **v1.1 with thread-safe execution**
- [x] Created Scene Generation Script (`generate_island.py`)
- [x] Created Bridge Runner (`run_via_bridge.py`)

---

## 🔧 Setup Instructions

### Step 1: Install the Blender Addon

1. **Close Blender completely** (if it's running)
2. Open Blender
3. Go to **Edit → Preferences → Add-ons**
4. Click **Install...**
5. Navigate to and select: `D:\blender\blender_mcp_bridge\antigravity_blender_addon.py`
6. **Enable** the addon by checking the box next to "Development: Antigravity Blender Bridge"
7. Close Preferences

### Step 2: Start the Bridge Server in Blender

1. In the 3D Viewport, press **N** to open the sidebar
2. Click the **Antigravity** tab
3. Click **Start Bridge Server**
4. You should see "Status: Running on port 8081" in the panel

### Step 3: Run a Script from the Terminal

Open a terminal in the project directory and run:

```powershell
cd D:\blender\blender_mcp_bridge
.\venv\Scripts\python run_via_bridge.py
```

This will send `generate_island.py` to Blender and execute it!

---

## 📁 File Descriptions

| File | Purpose |
|------|---------|
| `antigravity_blender_addon.py` | Blender addon that runs a server inside Blender to receive commands |
| `antigravity_blender_server.py` | MCP server for AI clients (Claude, Antigravity) to connect via MCP protocol |
| `run_via_bridge.py` | Standalone script to send Python files directly to Blender |
| `generate_island.py` | Example scene generator - creates a low-poly island with house |

---

## 🔍 Troubleshooting

### "Connection Refused" Error
- Make sure Blender is running
- Make sure the addon is enabled (Preferences → Add-ons → search "Antigravity")
- Click **Start Bridge Server** in the Antigravity sidebar panel

### "Timeout" Error
- The script may be taking too long. Check Blender's console for errors.
- Try restarting the Bridge Server (Stop → Start)

### "Address already in use" Error
- Close any other terminals that might be running the server
- Close and reopen Blender

### Script runs but nothing appears in Blender
- Check Blender's System Console (Window → Toggle System Console) for error messages
- Make sure you're looking at the right viewport (the objects might be created but the camera isn't centered on them)

---

## 🚀 Advanced Usage

### Running Custom Code

You can use `run_via_bridge.py` as a library:

```python
from run_via_bridge import run_code, get_scene_info

# Execute custom code
result = run_code("bpy.ops.mesh.primitive_cube_add()")
print(result)

# Get scene info
info = get_scene_info()
print(info)
```

### Using with MCP Clients (Antigravity/Claude)

The MCP server provides two tools:
- `run_blender_script(script_code)` - Execute Python code in Blender
- `get_scene_data()` - Get list of objects and collections

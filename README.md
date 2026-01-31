# Antigravity Blender MCP Bridge

A robust bridge for connecting Antigravity (or any MCP client) with Blender.

## Architecture

```
┌─────────────────┐     MCP/stdio     ┌─────────────────────────┐
│   Antigravity   │◄────────────────► │ antigravity_blender_    │
│   (AI Agent)    │                   │ server.py               │
└─────────────────┘                   └───────────┬─────────────┘
                                                  │ TCP Socket
                                                  │ (port 8081)
                                                  ▼
                                      ┌─────────────────────────┐
                                      │  blender_server.py      │
                                      │  (runs inside Blender)  │
                                      └─────────────────────────┘
```

## Quick Start

### 1. Start Blender with the Server

```bash
blender --background --python blender_server.py
```

Or for interactive mode (see the viewport):
```bash
blender --python blender_server.py
```

### 2. Run a Script

```powershell
.\venv\Scripts\python run_via_bridge.py
```

This will execute `generate_island.py` and create the island scene.

---

## Files

| File | Purpose |
|------|---------|
| `blender_server.py` | Socket server that runs inside Blender. Receives scripts and executes them. |
| `antigravity_blender_server.py` | MCP server for AI clients to connect via MCP protocol. |
| `run_via_bridge.py` | Standalone script runner - sends scripts directly to Blender. |
| `generate_island.py` | Example: Creates a low-poly island scene. |
| `antigravity_blender_addon.py` | (Legacy) Blender addon version - use `blender_server.py` instead. |

---

## Key Design Principles

### ✅ Guaranteed Response Contract
Every script execution returns a response:
- `{"status": "ok"}` on success
- `{"status": "error", "error": "...", "trace": "..."}` on failure
- `{"status": "progress", "message": "..."}` for progress updates

### ✅ Thread-Safe Execution
The server handles each connection in a separate thread, preventing deadlocks.

### ✅ No UI Dependencies
Scripts use `bpy.data.*` APIs instead of `bpy.ops.*` operators, making them safe for background execution.

### ✅ Progress Reporting
Scripts can call `send_status("message")` to report progress back to the client.

---

## Writing Scripts for Blender

```python
import bpy

def main():
    send_status("Starting...")
    
    # Use bpy.data.* APIs
    mesh = bpy.data.meshes.new("MyMesh")
    obj = bpy.data.objects.new("MyObject", mesh)
    bpy.context.collection.objects.link(obj)
    
    send_status("Done!")

main()
```

### Rules:
1. **Always define and call `main()`**
2. **Use `send_status()` for progress**
3. **Use `bpy.data.*` instead of `bpy.ops.*`**
4. **No infinite loops**
5. **Handle exceptions**

---

## Troubleshooting

### "Connection Refused"
- Blender server isn't running
- Run: `blender --background --python blender_server.py`

### "Timeout"
- Script is taking too long
- Check Blender's console for errors
- Make sure script calls `main()` at the end

### Port already in use
- Another instance is running
- Kill existing Blender processes
- Or change `PORT` in both `blender_server.py` and `run_via_bridge.py`

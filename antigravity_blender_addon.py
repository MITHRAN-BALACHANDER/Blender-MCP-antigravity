bl_info = {
    "name": "Antigravity Blender Bridge",
    "author": "Antigravity",
    "version": (1, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Antigravity",
    "description": "Bridge for Antigravity MCP Server - enables AI to control Blender",
    "warning": "",
    "wiki_url": "",
    "category": "Development",
}

import bpy
import socket
import threading
import json
import sys
import io
import traceback
import queue
from contextlib import redirect_stdout, redirect_stderr

# Global variables
server_thread = None
server_running = False
PORT = 8081

# Queue for thread-safe communication with main thread
command_queue = queue.Queue()
result_queue = queue.Queue()

def execute_script_on_main_thread(script_content):
    """Execute a script and return the result. Called from main thread via timer."""
    f_out = io.StringIO()
    try:
        with redirect_stdout(f_out), redirect_stderr(f_out):
            exec(script_content, {"bpy": bpy, "__builtins__": __builtins__})
        output = f_out.getvalue()
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "message": f"{str(e)}\n{traceback.format_exc()}"}

def get_scene_data_on_main_thread():
    """Get scene data. Called from main thread via timer."""
    try:
        data = {
            "objects": [obj.name for obj in bpy.data.objects],
            "collections": [col.name for col in bpy.data.collections],
            "active_object": bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
        }
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_command_queue():
    """Timer callback to process commands from the queue on the main thread."""
    try:
        while not command_queue.empty():
            cmd = command_queue.get_nowait()
            cmd_type = cmd.get("type")
            
            if cmd_type == "script":
                result = execute_script_on_main_thread(cmd.get("content", ""))
            elif cmd_type == "get_scene_data":
                result = get_scene_data_on_main_thread()
            else:
                result = {"status": "error", "message": f"Unknown command type: {cmd_type}"}
            
            result_queue.put(result)
            command_queue.task_done()
    except Exception as e:
        print(f"Error processing command: {e}")
    
    # Return time until next call (0.1 seconds) to keep timer running
    if server_running:
        return 0.1
    return None  # Stop timer when server stops

def handle_client(conn, addr):
    """Handle individual client connections."""
    print(f"[Antigravity Bridge] Connected by {addr}")
    try:
        # Set timeout for receiving data
        conn.settimeout(5.0)
        
        # Read length (4 bytes)
        length_bytes = conn.recv(4)
        if not length_bytes:
            print(f"[Antigravity Bridge] No data received from {addr}")
            return
        message_length = int.from_bytes(length_bytes, byteorder='big')
        print(f"[Antigravity Bridge] Expecting {message_length} bytes")
        
        # Read message
        data = b""
        while len(data) < message_length:
            packet = conn.recv(min(4096, message_length - len(data)))
            if not packet:
                break
            data += packet
        
        print(f"[Antigravity Bridge] Received {len(data)} bytes")
        request = json.loads(data.decode('utf-8'))
        
        # Queue the command for main thread execution
        command_queue.put(request)
        
        # Wait for result with timeout
        try:
            result = result_queue.get(timeout=30.0)  # 30 second timeout for script execution
        except queue.Empty:
            result = {"status": "error", "message": "Timeout waiting for Blender to execute command"}
        
        # Send response
        response_json = json.dumps(result).encode('utf-8')
        conn.sendall(len(response_json).to_bytes(4, byteorder='big'))
        conn.sendall(response_json)
        print(f"[Antigravity Bridge] Sent response to {addr}")
        
    except socket.timeout:
        print(f"[Antigravity Bridge] Timeout with client {addr}")
    except Exception as e:
        print(f"[Antigravity Bridge] Error handling request: {e}")
        traceback.print_exc()
    finally:
        conn.close()

def start_server_thread():
    """Server thread function - handles socket connections."""
    global server_running
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', PORT))
            s.listen(5)
            s.settimeout(1.0)
            print(f"[Antigravity Bridge] Server listening on port {PORT}")
            
            while server_running:
                try:
                    conn, addr = s.accept()
                    # Handle each client in a separate thread for responsiveness
                    client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if server_running:
                        print(f"[Antigravity Bridge] Server error: {e}")
    except OSError as e:
        print(f"[Antigravity Bridge] Could not start server: {e}")

class ANTIGRAVITY_OT_start_server(bpy.types.Operator):
    """Start the Antigravity Bridge Server"""
    bl_idname = "antigravity.start_server"
    bl_label = "Start Bridge Server"

    def execute(self, context):
        global server_thread, server_running
        
        if server_thread and server_thread.is_alive():
            self.report({'WARNING'}, "Server already running")
            return {'CANCELLED'}
        
        # Clear any stale data from queues
        while not command_queue.empty():
            try:
                command_queue.get_nowait()
            except queue.Empty:
                break
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                break
        
        server_running = True
        
        # Start the timer to process commands on main thread
        bpy.app.timers.register(process_command_queue, first_interval=0.1)
        
        # Start the server thread
        server_thread = threading.Thread(target=start_server_thread, daemon=True)
        server_thread.start()
        
        self.report({'INFO'}, f"Antigravity Bridge started on port {PORT}")
        return {'FINISHED'}

class ANTIGRAVITY_OT_stop_server(bpy.types.Operator):
    """Stop the Antigravity Bridge Server"""
    bl_idname = "antigravity.stop_server"
    bl_label = "Stop Bridge Server"

    def execute(self, context):
        global server_running
        server_running = False
        self.report({'INFO'}, "Server stopping...")
        return {'FINISHED'}

class ANTIGRAVITY_PT_main_panel(bpy.types.Panel):
    """Creates a Panel in the View3D UI"""
    bl_label = "Antigravity Bridge"
    bl_idname = "ANTIGRAVITY_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Antigravity"

    def draw(self, context):
        layout = self.layout
        
        global server_running
        if server_running:
            layout.label(text=f"Status: Running on port {PORT}", icon='PLAY')
        else:
            layout.label(text="Status: Stopped", icon='PAUSE')
        
        row = layout.row()
        row.operator("antigravity.start_server", icon='PLAY')
        row.operator("antigravity.stop_server", icon='PAUSE')

classes = (
    ANTIGRAVITY_OT_start_server,
    ANTIGRAVITY_OT_stop_server,
    ANTIGRAVITY_PT_main_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    global server_running
    server_running = False
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()

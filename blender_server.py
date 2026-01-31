"""
Blender MCP Server - Run with: blender --background --python blender_server.py

This server:
- Runs in Blender's background mode
- Handles connections in separate threads
- ALWAYS returns a response (success or error)
- Never blocks the main thread
- Provides progress reporting via send_status()
"""

import socket
import json
import traceback
import threading
import bpy

HOST = "127.0.0.1"
PORT = 8081

def handle_client(conn, addr):
    """Handle a single client connection with guaranteed response."""
    print(f"[BlenderMCP] Client connected: {addr}")
    
    try:
        # Receive data (up to 1MB)
        data = b""
        conn.settimeout(5.0)  # 5 second timeout for receiving
        
        while True:
            try:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                # Check if we have a complete JSON object
                try:
                    json.loads(data.decode())
                    break  # Valid JSON, stop receiving
                except json.JSONDecodeError:
                    continue  # Keep receiving
            except socket.timeout:
                break
        
        if not data:
            send_response(conn, {"status": "error", "error": "No data received"})
            return
        
        cmd = json.loads(data.decode())
        script = cmd.get("script", "")
        
        if not script:
            send_response(conn, {"status": "error", "error": "No script provided"})
            return
        
        # Send initial status
        send_response(conn, {"status": "running", "message": "Script execution started"})
        
        # Create execution environment with send_status helper
        def send_status(msg):
            """Send progress update to client."""
            send_response(conn, {"status": "progress", "message": msg})
        
        exec_env = {
            "bpy": bpy,
            "send_status": send_status,
            "__builtins__": __builtins__,
        }
        
        # Execute the script
        try:
            exec(script, exec_env)
            send_response(conn, {"status": "ok", "message": "Script completed successfully"})
        except Exception as e:
            send_response(conn, {
                "status": "error",
                "error": str(e),
                "trace": traceback.format_exc()
            })
    
    except Exception as e:
        try:
            send_response(conn, {
                "status": "error",
                "error": f"Server error: {str(e)}",
                "trace": traceback.format_exc()
            })
        except:
            pass
    finally:
        try:
            conn.close()
        except:
            pass
        print(f"[BlenderMCP] Client disconnected: {addr}")


def send_response(conn, payload):
    """Send a JSON response to the client."""
    try:
        response = json.dumps(payload) + "\n"
        conn.sendall(response.encode())
    except Exception as e:
        print(f"[BlenderMCP] Error sending response: {e}")


def main():
    """Main server loop."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    
    print("=" * 50)
    print(f"[BlenderMCP] Server running on {HOST}:{PORT}")
    print("[BlenderMCP] Waiting for connections...")
    print("=" * 50)
    
    try:
        while True:
            conn, addr = server.accept()
            # Handle each client in a separate thread
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[BlenderMCP] Server shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()

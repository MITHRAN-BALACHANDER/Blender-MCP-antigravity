"""
Standalone script to send commands to Blender via the bridge.
Does NOT require MCP - talks directly to Blender.

Usage:
    python run_via_bridge.py                    # Run generate_island.py
    python run_via_bridge.py myscript.py        # Run custom script
"""

import socket
import json
import sys
import os

BLENDER_HOST = "127.0.0.1"
BLENDER_PORT = 8081
TIMEOUT = 120


def send_script(script: str) -> None:
    """Send a script to Blender and print all responses."""
    
    print(f"Connecting to Blender at {BLENDER_HOST}:{BLENDER_PORT}...")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(TIMEOUT)
        s.connect((BLENDER_HOST, BLENDER_PORT))
        print("Connected!")
        
        # Send the script
        payload = json.dumps({"script": script})
        print(f"Sending {len(payload)} bytes...")
        s.sendall(payload.encode())
        print("Sent! Waiting for responses...\n")
        
        # Collect all responses
        buffer = ""
        final_status = None
        
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
                            status = msg.get("status", "unknown")
                            
                            if status == "progress":
                                print(f"  [PROGRESS] {msg.get('message', '')}")
                            elif status == "running":
                                print(f"  [RUNNING] {msg.get('message', 'Execution started')}")
                            elif status == "ok":
                                print(f"  [SUCCESS] {msg.get('message', 'Complete')}")
                                final_status = "ok"
                            elif status == "error":
                                print(f"  [ERROR] {msg.get('error', 'Unknown error')}")
                                if msg.get("trace"):
                                    print(f"\nStack trace:\n{msg.get('trace')}")
                                final_status = "error"
                        except json.JSONDecodeError:
                            print(f"  [RAW] {line}")
                
                if final_status:
                    break
                    
            except socket.timeout:
                print("\n[TIMEOUT] Blender did not respond within timeout")
                final_status = "timeout"
                break
        
        s.close()
        
        print("\n" + "=" * 50)
        if final_status == "ok":
            print("SCRIPT EXECUTED SUCCESSFULLY!")
        elif final_status == "error":
            print("SCRIPT FAILED - See error above")
        else:
            print(f"FINISHED WITH STATUS: {final_status}")
        print("=" * 50)
        
    except ConnectionRefusedError:
        print("\n[ERROR] Could not connect to Blender!")
        print("\nMake sure Blender is running with the server:")
        print("  blender --background --python blender_server.py")
        print("\nOr if using the addon, start the Bridge Server from the Antigravity panel.")
    except Exception as e:
        print(f"\n[ERROR] {e}")


def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else "generate_island.py"
    
    print("=" * 50)
    print("Antigravity Blender Bridge - Script Runner")
    print("=" * 50)
    
    if not os.path.exists(script_path):
        print(f"Error: Script not found: {script_path}")
        return
    
    print(f"Loading script: {script_path}")
    
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()
    
    print(f"Script size: {len(script)} bytes")
    print("-" * 50)
    
    send_script(script)


if __name__ == "__main__":
    main()

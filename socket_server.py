import socket
import threading
import time
import queue # To communicate between server thread and main orchestrator

# Global variable to hold the currently connected Pi's socket
connected_pi_socket = None
# A queue to put messages from the Pi into for the orchestrator to pick up
pi_messages_queue = queue.Queue()

HOST = '0.0.0.0'
PORT = 65432

def handle_pi_client(conn, addr):
    """Handles continuous communication with the connected Raspberry Pi."""
    global connected_pi_socket
    connected_pi_socket = conn # Store the connection
    print(f"[Socket Server] Raspberry Pi connected from {addr}")
    
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"[Socket Server] Raspberry Pi {addr} disconnected gracefully.")
                break
            
            message_from_pi = data.decode().strip()
            print(f"[Socket Server] Received from Pi ({addr}): '{message_from_pi}'")
            pi_messages_queue.put(message_from_pi) # Put message into queue for orchestrator
            
    except ConnectionResetError:
        print(f"[Socket Server] Raspberry Pi {addr} forcefully closed the connection.")
    except Exception as e:
        print(f"[Socket Server] An error occurred with Pi {addr}: {e}")
    finally:
        connected_pi_socket = None # Clear connection on disconnect
        conn.close()
        print(f"[Socket Server] Connection with Pi {addr} closed.")

def start_socket_server():
    """Starts the main socket server thread."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1) # Listen for up to 1 connection (we expect only one Pi)
        print(f"[Socket Server] Listening on {HOST}:{PORT}")
        
        while True:
            conn, addr = s.accept() # Blocks until a client connects
            if connected_pi_socket and not connected_pi_socket._closed:
                print(f"[Socket Server] Warning: Another client ({addr}) tried to connect. Ignoring.")
                conn.close()
                continue
            
            # Start a new thread to handle this client
            client_handler_thread = threading.Thread(target=handle_pi_client, args=(conn, addr))
            client_handler_thread.daemon = True # Allows main program to exit if this is still running
            client_handler_thread.start()
            print(f"[Socket Server] Handler thread started for {addr}.")

def send_command_to_pi(command: str):
    """Sends a command to the connected Raspberry Pi."""
    global connected_pi_socket
    if connected_pi_socket and not connected_pi_socket._closed:
        try:
            print(f"[Socket Server] Sending command to Pi: '{command}'")
            connected_pi_socket.sendall(command.encode())
            return True
        except Exception as e:
            print(f"[Socket Server] Failed to send command to Pi (connection likely lost): {e}")
            connected_pi_socket = None # Mark as disconnected
            return False
    else:
        print("[Socket Server] No Raspberry Pi client is currently connected.")
        return False

def get_pi_message(timeout=0.1):
    """Retrieves a message from the Pi message queue."""
    try:
        return pi_messages_queue.get(timeout=timeout)
    except queue.Empty:
        return None

def is_pi_connected():
    """Checks if the Raspberry Pi is currently connected."""
    return connected_pi_socket is not None and not connected_pi_socket._closed
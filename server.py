#!/usr/bin/env python3
import socket
import threading
import json
import os
import base64

HOST = '0.0.0.0'
PORT = 5000

# Thread-safe client list
clients_lock = threading.Lock()
clients = []    # List of tuples (client_socket, username)
history = []    # List of message dicts for chat history

def broadcast(message, exclude_socket=None):
    """Send a message to all connected clients, excluding exclude_socket if provided."""
    with clients_lock:
        for client, username in clients:
            if client != exclude_socket:
                try:
                    client.sendall(message.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending to {username}: {e}")
                    client.close()
                    clients.remove((client, username))

def handle_client(client_socket, address):
    """Handle incoming messages from a single client."""
    global clients, history
    username = None
    try:
        raw = client_socket.recv(1024).decode('utf-8')
        init_msg = json.loads(raw)
        if init_msg.get('type') != 'auth' or 'username' not in init_msg:
            client_socket.sendall('Authentication failed'.encode('utf-8'))
            client_socket.close()
            return
        username = init_msg['username']

        with clients_lock:
            clients.append((client_socket, username))
        print(f"{username} connected from {address}")

        # Send chat history to the new client
        for msg in history:
            client_socket.sendall((json.dumps(msg) + "\n").encode('utf-8'))

        while True:
            raw_data = client_socket.recv(4096).decode('utf-8')
            if not raw_data:
                break
            messages = raw_data.split("\n")
            for raw in messages:
                if not raw.strip():
                    continue
                msg_obj = json.loads(raw)
                msg_type = msg_obj.get('type')

                if msg_type == 'msg':
                    msg_obj['username'] = username
                    history.append(msg_obj)
                    print(f"[{username}] says: {msg_obj['content']}")
                    broadcast(json.dumps(msg_obj) + "\n", exclude_socket=client_socket)

                elif msg_type == 'file':
                    filename = msg_obj.get('filename')
                    content = msg_obj.get('content')
                    os.makedirs('files', exist_ok=True)
                    filepath = os.path.join('files', filename)
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(content))
                    msg_obj['username'] = username
                    history.append(msg_obj)
                    print(f"[{username}] uploaded file: {filename}")
                    broadcast(json.dumps(msg_obj) + "\n", exclude_socket=client_socket)

                elif msg_type == 'download_request':
                    filename = msg_obj.get('filename')
                    filepath = os.path.join('files', filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            file_data = f.read()
                        response = {
                            'type': 'file_download',
                            'filename': filename,
                            'content': base64.b64encode(file_data).decode('utf-8'),
                            'username': 'server'
                        }
                    else:
                        response = {'type': 'error', 'message': f'File {filename} not found'}
                    client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))

                else:
                    response = {'type': 'error', 'message': 'Unknown message type'}
                    client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))

    except Exception as e:
        print(f"Connection error with {address}: {e}")
    finally:
        if username:
            print(f"{username} disconnected")
        with clients_lock:
            clients[:] = [(c, u) for c, u in clients if c != client_socket]
        client_socket.close()


def main():
    print(f"Starting chat server on {HOST}:{PORT}")
    print("Press Ctrl+C to stop the server.")

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((HOST, PORT))
    server_sock.listen(5)

    while True:
        client_sock, addr = server_sock.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()

if __name__ == '__main__':
    main()
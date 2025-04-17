#!/usr/bin/env python3
import socket
import threading
import json
import os
import base64


def receive_messages(sock):
    """Continuously receive and display messages from the server."""
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                print("Disconnected from server.")
                break
            messages = data.split("\n")
            for msg in messages:
                if not msg.strip():
                    continue
                msg_obj = json.loads(msg)
                msg_type = msg_obj.get('type')

                if msg_type == 'msg':
                    print(f"\n[{msg_obj['username']}] {msg_obj['content']}")
                elif msg_type == 'file':
                    print(f"\n[{msg_obj['username']}] uploaded file: {msg_obj['filename']}")
                elif msg_type == 'file_download':
                    filename = msg_obj.get('filename')
                    content = msg_obj.get('content')
                    local_path = 'received_' + filename
                    with open(local_path, 'wb') as f:
                        f.write(base64.b64decode(content))
                    print(f"\n[server] downloaded file saved to {local_path}")
                elif msg_type == 'error':
                    print(f"\n[Error] {msg_obj.get('message')}")
                else:
                    print(f"\n[Unknown] {msg_obj}")
            print('> ', end='', flush=True)
        except Exception as e:
            print(f"Error receiving: {e}")
            break


def main():
    print("Welcome to the Chat Client")
    server_ip = input('Enter server IP: ')
    port_input = input('Enter server port (default 5000): ')
    server_port = int(port_input) if port_input else 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    username = input('Enter your username: ')
    auth_msg = {'type': 'auth', 'username': username}
    sock.sendall((json.dumps(auth_msg) + "\n").encode('utf-8'))

    print("Connected to chat server.")
    print("Type messages and press Enter to send.")
    print("Commands:")
    print("  /upload <file_path>   Upload a file to the server.")
    print("  /download <filename>  Download a file from the server (use only the filename, not path).\n")

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    while True:
        user_input = input('> ')
        if user_input.startswith('/upload '):
            raw_path = user_input.split(maxsplit=1)[1]
            file_path = os.path.abspath(os.path.expanduser(raw_path))
            if not os.path.isfile(file_path):
                print(f"File not found: {file_path}")
                continue
            filename = os.path.basename(file_path)
            with open(file_path, 'rb') as f:
                file_data = f.read()
            encoded_content = base64.b64encode(file_data).decode('utf-8')
            msg_obj = {'type': 'file', 'filename': filename, 'content': encoded_content}
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))

        elif user_input.startswith('/download '):
            raw = user_input.split(maxsplit=1)[1]
            filename = os.path.basename(os.path.expanduser(raw))
            msg_obj = {'type': 'download_request', 'filename': filename}
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))

        else:
            msg_obj = {'type': 'msg', 'content': user_input}
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))

if __name__ == '__main__':
    main()
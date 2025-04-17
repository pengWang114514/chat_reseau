# chat_reseau
projet of chat_ameliore
CNS M1 SR Wang Zhipeng
# Chat Server and Client

## Overview
This project implements a simple chat application with file upload/download functionality, based on a client-server architecture using TCP sockets.

- The **server** manages connected clients, broadcasts messages, stores message history, and handles file storage and download requests.
- The **client** connects to the server, sends text messages or files, and receives messages and files from others.

## Prerequisites
- **Operating System**: Debian 12
- **Python**: version 3.6 or higher (please pre-installed on Debian 12)

## Setup and Usage
1. **Clone or download** this repository onto your Debian 12 machine.
2. **Ensure Python 3 is installed**:
   Verify Your version of Python:
   python3 --version

### Server
1. Open a terminal in the project directory.
2. Run:
   python3 server.py
3. The server listens on port **5000** by default.
4. To stop the server, press **Ctrl+C**.

### Client
1. Open another terminal (can be on the same or a different Debian 12 machine).
2. Run:
   python3 client.py
3. Follow the prompts:
   - **Server IP**: IP address of the server (e.g., '192.168.36.160')
   - **Server port**: Press Enter to accept default '5000'
   - **Username**: Choose any name to identify yourself in the chat,e.g. 'Lapeng'
4. After connecting, you can:
   - **Send a text message**: Type your message and press Enter
   - **Upload a file**: Use the command:
     /upload <file_path>
    
     Example:
     /upload ~/chat_project/README.md
     
   - **Download a file**: Use the command:
     /download <filename>
     
     Example (only filename, no path):
     /download README.md

## File Storage
- Uploaded files are stored in the server's 'files/' directory.
- Downloaded files are saved in the client's working directory with the prefix 'received_', e.g., 'received_README.md'.



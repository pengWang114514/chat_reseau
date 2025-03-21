#!/usr/bin/env python3
import socket
import threading
import json
import os
import base64

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                break
            # 可能包含多条消息，用换行符分割
            messages = data.split("\n")
            for msg in messages:
                if not msg.strip():
                    continue
                try:
                    msg_obj = json.loads(msg)
                    msg_type = msg_obj.get("type")
                    if msg_type == "msg":
                        print(f"\n[{msg_obj.get('username')}] {msg_obj.get('content')}")
                    elif msg_type == "file":
                        print(f"\n[{msg_obj.get('username')}] 上传了文件：{msg_obj.get('filename')}")
                    elif msg_type == "file_download":
                        # 将收到的文件保存到本地，文件名前加上 "recv_"
                        filename = msg_obj.get("filename")
                        content = msg_obj.get("content")
                        file_path = "recv_" + filename
                        with open(file_path, "wb") as f:
                            f.write(base64.b64decode(content))
                        print(f"\n[server] 文件 {filename} 已下载，保存在 {file_path}")
                    elif msg_type == "error":
                        print(f"\n[错误] {msg_obj.get('message')}")
                    else:
                        print("\n[未知消息]", msg_obj)
                except Exception as e:
                    print("处理消息时错误：", e)
        except Exception as e:
            print("连接关闭：", e)
            break

def main():
    server_ip = input("请输入服务器 IP：")
    port_input = input("请输入服务器端口（默认 5000）：")
    server_port = int(port_input) if port_input else 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    username = input("请输入你的用户名：")
    # 发送认证信息
    auth_msg = {"type": "auth", "username": username}
    sock.sendall((json.dumps(auth_msg) + "\n").encode('utf-8'))

    # 启动接收消息线程
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    print("命令说明：直接输入文字发送消息；")
    print("上传文件命令：/upload 文件路径")
    print("下载文件命令：/download 文件名")
    while True:
        user_input = input(">> ")
        if user_input.startswith("/upload "):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("用法：/upload 文件路径")
                continue
            file_path = parts[1]
            if not os.path.isfile(file_path):
                print("文件不存在！")
                continue
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                file_data = f.read()
            encoded_content = base64.b64encode(file_data).decode('utf-8')
            msg_obj = {
                "type": "file",
                "filename": filename,
                "content": encoded_content
            }
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))
        elif user_input.startswith("/download "):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("用法：/download 文件名")
                continue
            filename = parts[1]
            msg_obj = {
                "type": "download_request",
                "filename": filename
            }
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))
        else:
            # 发送普通文本消息
            msg_obj = {"type": "msg", "content": user_input}
            sock.sendall((json.dumps(msg_obj) + "\n").encode('utf-8'))

if __name__ == '__main__':
    main()

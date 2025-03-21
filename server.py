#!/usr/bin/env python3
import socket
import threading
import json
import os
import base64

HOST = '0.0.0.0'
PORT = 5000

# 线程同步保护客户端列表
clients_lock = threading.Lock()
clients = []  # 存放 (client_socket, username)
history = []  # 聊天历史记录，每条消息均为字典对象

def broadcast(message, exclude_socket=None):
    """将消息字符串广播给所有客户端（除 exclude_socket 外）"""
    with clients_lock:
        for client, username in clients:
            if client != exclude_socket:
                try:
                    client.sendall(message.encode('utf-8'))
                except Exception as e:
                    print(f"向 {username} 发送消息错误：{e}")
                    client.close()
                    clients.remove((client, username))

def handle_client(client_socket, addr):
    global clients, history
    try:
        # 第一个消息应为认证消息，格式为 JSON，包含 type="auth" 和 username 字段
        data = client_socket.recv(1024).decode('utf-8')
        if not data:
            client_socket.close()
            return
        try:
            init_msg = json.loads(data)
            if init_msg.get("type") != "auth" or "username" not in init_msg:
                client_socket.sendall("认证信息错误".encode('utf-8'))
                client_socket.close()
                return
            username = init_msg["username"]
        except Exception:
            client_socket.sendall("认证失败".encode('utf-8'))
            client_socket.close()
            return

        with clients_lock:
            clients.append((client_socket, username))
        print(f"{username}({addr}) 已连接")

        # 发送历史记录给新连接的客户端（每条记录一行）
        for msg in history:
            try:
                client_socket.sendall((json.dumps(msg) + "\n").encode('utf-8'))
            except Exception as e:
                print("发送历史记录出错：", e)

        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break
            # 接收到的可能是多条 JSON 消息，用换行符分隔
            messages = data.split("\n")
            for m in messages:
                if not m.strip():
                    continue
                try:
                    msg_obj = json.loads(m)
                    msg_type = msg_obj.get("type")
                    if msg_type == "msg":
                        # 文本消息：添加发送者信息，存入历史，并广播给其他客户端
                        msg_obj["username"] = username
                        history.append(msg_obj)
                        broadcast(json.dumps(msg_obj) + "\n", exclude_socket=client_socket)
                    elif msg_type == "file":
                        # 文件上传消息，字段包括：filename、content（内容经过 Base64 编码）
                        filename = msg_obj.get("filename")
                        content = msg_obj.get("content")
                        # 确保存放文件的目录存在
                        if not os.path.exists("files"):
                            os.makedirs("files")
                        file_path = os.path.join("files", filename)
                        with open(file_path, "wb") as f:
                            f.write(base64.b64decode(content))
                        msg_obj["username"] = username
                        history.append(msg_obj)
                        broadcast(json.dumps(msg_obj) + "\n", exclude_socket=client_socket)
                    elif msg_type == "download_request":
                        # 文件下载请求：字段 filename
                        filename = msg_obj.get("filename")
                        file_path = os.path.join("files", filename)
                        if os.path.exists(file_path):
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                            response = {
                                "type": "file_download",
                                "filename": filename,
                                "content": base64.b64encode(file_data).decode('utf-8'),
                                "username": "server"
                            }
                        else:
                            response = {
                                "type": "error",
                                "message": f"文件 {filename} 不存在"
                            }
                        client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))
                    else:
                        # 未知消息类型
                        response = {"type": "error", "message": "未知的消息类型"}
                        client_socket.sendall((json.dumps(response) + "\n").encode('utf-8'))
                except Exception as e:
                    print("处理消息时出错：", e)
    except Exception as e:
        print("与客户端通信异常：", e)
    finally:
        print(f"客户端 {addr} 断开连接")
        with clients_lock:
            for c, uname in clients:
                if c == client_socket:
                    clients.remove((c, uname))
                    break
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"服务器已启动，监听 {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == '__main__':
    main()

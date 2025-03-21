#!/usr/bin/env python3
import socket
import threading
import json
import hashlib
import base64
import os
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

# 辅助函数：补足明文长度到 16 的倍数
def pad(text):
    bs = 16
    padding = bs - len(text.encode('utf-8')) % bs
    return text + ('\0' * padding)

# 加密函数：返回十六进制字符串
def encrypt(plaintext, key):
    plaintext = pad(plaintext)
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(plaintext.encode('utf-8'))
    return b2a_hex(encrypted).decode('utf-8')

# 解密函数
def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(a2b_hex(ciphertext))
    return decrypted.decode('utf-8').rstrip('\0')

# 线程函数：接收服务器发送的消息
def receive_messages(sock, key):
    while True:
        try:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                break
            json_str = decrypt(data, key)
            message_obj = json.loads(json_str)
            if message_obj['type'] == 'msg':
                print(f"\n[{message_obj['username']}] {message_obj['content']}")
            elif message_obj['type'] == 'file':
                filename = message_obj['filename']
                filedata = base64.b64decode(message_obj['content'])
                # 将收到的文件保存到本地，文件名前加上 "recv_"
                with open("recv_" + filename, "wb") as f:
                    f.write(filedata)
                print(f"\n[{message_obj['username']}] 发送了文件：{filename}（已保存为 recv_{filename}）")
            print(">> ", end="", flush=True)
        except Exception as e:
            print("接收消息错误：", e)
            break

# 线程函数：发送用户输入的消息
def send_messages(sock, username, key):
    while True:
        msg = input(">> ")
        if msg.startswith("/file "):
            # 格式：/file 文件路径
            parts = msg.split(maxsplit=1)
            if len(parts) == 2:
                filepath = parts[1]
                if not os.path.isfile(filepath):
                    print("文件不存在！")
                    continue
                with open(filepath, 'rb') as f:
                    filedata = f.read()
                encoded_data = base64.b64encode(filedata).decode('utf-8')
                filename = os.path.basename(filepath)
                message_obj = {
                    "type": "file",
                    "filename": filename,
                    "content": encoded_data
                }
            else:
                print("使用格式：/file 文件路径")
                continue
        else:
            message_obj = {
                "type": "msg",
                "content": msg
            }
        json_str = json.dumps(message_obj)
        encrypted_msg = encrypt(json_str, key)
        sock.sendall(encrypted_msg.encode('utf-8'))

def main():
    server_ip = input("请输入服务器 IP： ")
    server_port = int(input("请输入服务器端口（默认 5000）： ") or 5000)
    key_input = input("请输入共享密钥（必须与服务器一致）： ")
    k1 = hashlib.sha256(key_input.encode('utf-8')).hexdigest()
    k2 = hashlib.sha256(k1.encode('utf-8')).hexdigest()
    key = k2[6:38].encode('utf-8')
    
    username = input("请输入你的用户名： ")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    # 连接后先发送加密后的用户名
    encrypted_username = encrypt(username, key)
    sock.sendall(encrypted_username.encode('utf-8'))
    
    # 开启接收消息线程
    recv_thread = threading.Thread(target=receive_messages, args=(sock, key))
    recv_thread.daemon = True
    recv_thread.start()
    
    # 主线程负责发送消息
    send_messages(sock, username, key)
    
if __name__ == '__main__':
    main()

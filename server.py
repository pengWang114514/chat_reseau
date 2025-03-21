#!/usr/bin/env python3
import socket
import threading
import json
import hashlib
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

# 全局变量
clients = []      # 保存 (client_socket, username)
history = []      # 聊天记录，存储每条消息（JSON 对象）

# 辅助函数：对明文补位，确保长度为 16 的倍数
def pad(text):
    bs = 16
    padding = bs - len(text.encode('utf-8')) % bs
    return text + ('\0' * padding)

# 加密函数：对字符串进行 AES 加密，返回十六进制字符串
def encrypt(plaintext, key):
    plaintext = pad(plaintext)
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(plaintext.encode('utf-8'))
    return b2a_hex(encrypted).decode('utf-8')

# 解密函数：对十六进制加密字符串解密，返回明文
def decrypt(ciphertext, key):
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(a2b_hex(ciphertext))
    return decrypted.decode('utf-8').rstrip('\0')

# 将消息广播给除发送者之外的所有客户端
def broadcast(message, sender_socket, key):
    for client, username in clients:
        if client != sender_socket:
            try:
                client.sendall(message.encode('utf-8'))
            except:
                client.close()
                remove_client(client)

def remove_client(client_socket):
    global clients
    for c, username in clients:
        if c == client_socket:
            clients.remove((c, username))
            break

# 处理每个客户端连接
def handle_client(client_socket, addr, key):
    global clients, history
    try:
        # 第一个接收到的加密消息为用户名
        data = client_socket.recv(4096).decode('utf-8')
        username = decrypt(data, key)
        print(f"客户端 {addr} 以用户名 {username} 连接")
        clients.append((client_socket, username))
        # 将历史聊天记录发给新连接的客户端
        for msg in history:
            json_str = json.dumps(msg)
            encrypted_msg = encrypt(json_str, key)
            client_socket.sendall(encrypted_msg.encode('utf-8'))
        # 循环接收客户端消息
        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                break
            try:
                json_str = decrypt(data, key)
                message_obj = json.loads(json_str)
                # 为消息附上发送者信息
                message_obj['username'] = username
                print(f"收到 {username} 的消息: {message_obj}")
                # 保存到历史记录
                history.append(message_obj)
                # 重新加密后转发给其他客户端
                encrypted_broadcast = encrypt(json.dumps(message_obj), key)
                broadcast(encrypted_broadcast, client_socket, key)
            except Exception as e:
                print("处理消息错误：", e)
    except Exception as e:
        print("客户端连接异常：", e)
    finally:
        print(f"客户端 {addr} 断开连接")
        remove_client(client_socket)
        client_socket.close()

def main():
    host = '0.0.0.0'
    port = 5000

    # 输入共享密钥，使用两次 SHA-256 哈希生成 AES 密钥（取部分字符，保证 16 字节）
    key_input = input("请输入共享密钥（密钥必须与客户端一致）： ")
    k1 = hashlib.sha256(key_input.encode('utf-8')).hexdigest()
    k2 = hashlib.sha256(k1.encode('utf-8')).hexdigest()
    key = k2[6:38].encode('utf-8')
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"服务器启动，监听 {host}:{port}")
    
    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr, key))
        client_thread.daemon = True
        client_thread.start()

if __name__ == '__main__':
    main()

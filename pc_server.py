import socket
import threading
import os
import time
import hashlib
import struct

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print("=" * 60)
    print("PC聊天服务器 (支持文件传输) - 修复版")
    print("=" * 60)

def get_file_checksum(file_path):
    """计算文件的MD5校验和"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def recv_all(sock, length):
    """接收指定长度的数据"""
    data = b''
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            return None
        data += packet
    return data

def handle_client(client_socket, client_address):
    def receive_thread():
        while True:
            try:
                # 读取消息类型 (1字节)
                msg_type = recv_all(client_socket, 1)
                if not msg_type:
                    break
                    
                if msg_type == b'T':  # 文本消息
                    # 读取文本长度 (4字节, 网络字节序)
                    text_len_data = recv_all(client_socket, 4)
                    if not text_len_data:
                        break
                    text_len = struct.unpack('!I', text_len_data)[0]
                    
                    # 接收文本内容
                    message = recv_all(client_socket, text_len).decode('utf-8')
                    print(f"\n手机 > {message}\nPC > ", end="", flush=True)
                    
                elif msg_type == b'F':  # 文件传输
                    # 读取文件名长度 (1字节)
                    name_len_data = recv_all(client_socket, 1)
                    if not name_len_data:
                        break
                    name_len = struct.unpack('B', name_len_data)[0]
                    
                    # 读取文件名
                    file_name = recv_all(client_socket, name_len).decode('utf-8')
                    
                    # 读取文件大小 (8字节, 网络字节序)
                    file_size_data = recv_all(client_socket, 8)
                    if not file_size_data:
                        break
                    file_size = struct.unpack('!Q', file_size_data)[0]
                    
                    # 读取MD5校验和 (32字节)
                    file_md5 = recv_all(client_socket, 32).decode('utf-8')
                    
                    print(f"\n接收文件中: {file_name} ({file_size/1024:.1f}KB)")
                    print(f"MD5校验: {file_md5}")
                    
                    # 创建接收目录
                    if not os.path.exists("received_files"):
                        os.makedirs("received_files")
                    
                    file_path = os.path.join("received_files", file_name)
                    received = 0
                    start_time = time.time()
                    
                    with open(file_path, "wb") as f:
                        while received < file_size:
                            chunk_size = min(4096, file_size - received)
                            chunk = recv_all(client_socket, chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            received += len(chunk)
                    
                    # 验证文件完整性
                    if received == file_size:
                        actual_md5 = get_file_checksum(file_path)
                        if actual_md5 == file_md5:
                            print(f"文件接收成功! 保存位置: {file_path}")
                            print(f"传输耗时: {time.time() - start_time:.2f}秒")
                        else:
                            print("文件校验失败! 传输可能已损坏")
                    else:
                        print(f"文件接收不完整! ({received}/{file_size} 字节)")
                    
                    print("PC > ", end="", flush=True)
                    
            except Exception as e:
                print(f"\n连接错误: {e}")
                break
    
    print(f"\n手机已连接: {client_address[0]}:{client_address[1]}")
    
    # 启动消息接收线程
    recv_thread = threading.Thread(target=receive_thread)
    recv_thread.daemon = True
    recv_thread.start()
    
    return client_socket

def send_text(sock, text):
    """发送文本消息"""
    encoded_text = text.encode('utf-8')
    # 消息类型: T (文本)
    sock.send(b'T')
    # 文本长度 (4字节, 网络字节序)
    sock.send(struct.pack('!I', len(encoded_text)))
    # 文本内容
    sock.send(encoded_text)

def send_file(sock, file_path):
    """发送文件"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
        
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_md5 = get_file_checksum(file_path)
    
    # 消息类型: F (文件)
    sock.send(b'F')
    
    # 发送文件名 (长度 + 内容)
    encoded_name = file_name.encode('utf-8')
    sock.send(struct.pack('B', len(encoded_name)))  # 文件名长度 (1字节)
    sock.send(encoded_name)                        # 文件名内容
    
    # 文件大小 (8字节, 网络字节序)
    sock.send(struct.pack('!Q', file_size))
    
    # MD5校验和 (32字节)
    sock.send(file_md5.encode('utf-8'))
    
    print(f"发送文件中: {file_name} ({file_size/1024:.1f}KB)")
    start_time = time.time()
    
    # 发送文件内容
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sock.send(chunk)
    
    print(f"文件发送完成! 耗时: {time.time() - start_time:.2f}秒")
    return True

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    
    print_banner()
    print(f"服务器已启动，监听 {host}:{port}")
    print(f"本机IP: {socket.gethostbyname(socket.gethostname())}")
    print("-" * 60)
    print("等待手机连接...")
    
    client, addr = server.accept()
    client_socket = handle_client(client, addr)
    
    try:
        while True:
            msg = input("PC > ")
            if not msg:
                continue
                
            if msg.lower() == 'exit':
                break
                
            if msg.startswith('/sendfile '):
                # 文件发送命令
                file_path = msg.split(' ', 1)[1]
                send_file(client_socket, file_path)
                print("PC > ", end="", flush=True)
                
            else:
                # 文本消息
                send_text(client_socket, msg)
                
    except KeyboardInterrupt:
        pass
    finally:
        client_socket.close()
        server.close()
        print("\n连接已关闭")

if __name__ == "__main__":
    start_server()

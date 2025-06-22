import socket
import threading
import os
import time
import hashlib

def clear_screen():
    os.system('clear')

def print_banner():
    clear_screen()
    print("=" * 60)
    print("Termux聊天客户端 (支持文件传输)")
    print("=" * 60)

def get_file_checksum(file_path):
    """计算文件的MD5校验和"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def start_client():
    print_banner()
    server_ip = input("输入PC的IP地址: ")
    server_port = 12345
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((server_ip, server_port))
        print(f"已连接到 {server_ip}:{server_port}")
        print("-" * 60)
        print("输入消息 (输入'exit'退出)")
        print("发送文件: /sendfile <文件路径>")
        print("=" * 60)
        
        def receive_thread():
            while True:
                try:
                    header = client.recv(50).decode('utf-8').strip()
                    if not header:
                        break
                    
                    if header.startswith("TEXT:"):
                        # 文本消息
                        msg_length = int(header.split(":")[1])
                        message = client.recv(msg_length).decode('utf-8')
                        print(f"\nPC > {message}\n手机 > ", end="", flush=True)
                        
                    elif header.startswith("FILE:"):
                        # 文件传输
                        _, file_name, file_size, file_md5 = header.split(":", 3)
                        file_size = int(file_size)
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
                                chunk = client.recv(min(4096, file_size - received))
                                if not chunk:
                                    break
                                f.write(chunk)
                                received += len(chunk)
                        
                        # 验证文件完整性
                        if get_file_checksum(file_path) == file_md5:
                            print(f"文件接收成功! 保存位置: {file_path}")
                            print(f"传输耗时: {time.time() - start_time:.2f}秒")
                        else:
                            print("文件校验失败! 传输可能已损坏")
                        
                        print("手机 > ", end="", flush=True)
                        
                except Exception as e:
                    print(f"\n连接错误: {e}")
                    break
        
        # 启动消息接收线程
        recv_thread = threading.Thread(target=receive_thread)
        recv_thread.daemon = True
        recv_thread.start()
        
        while True:
            msg = input("手机 > ")
            if not msg:
                continue
                
            if msg.lower() == 'exit':
                break
                
            if msg.startswith('/sendfile '):
                # 文件发送命令
                file_path = msg.split(' ', 1)[1]
                if not os.path.exists(file_path):
                    print(f"文件不存在: {file_path}")
                    continue
                    
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_md5 = get_file_checksum(file_path)
                
                # 发送文件头
                header = f"FILE:{file_name}:{file_size}:{file_md5}"
                client.send(header.ljust(50).encode('utf-8'))
                
                print(f"发送文件中: {file_name} ({file_size/1024:.1f}KB)")
                start_time = time.time()
                
                # 发送文件内容
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        client.send(chunk)
                
                print(f"文件发送完成! 耗时: {time.time() - start_time:.2f}秒")
                print("手机 > ", end="", flush=True)
                
            else:
                # 文本消息
                header = f"TEXT:{len(msg)}".ljust(50)
                client.send(header.encode('utf-8'))
                client.send(msg.encode('utf-8'))
                
    except Exception as e:
        print(f"连接错误: {e}")
    finally:
        client.close()
        print("连接已关闭")

if __name__ == "__main__":
    # 安装必要组件
    if not os.path.exists("/data/data/com.termux/files/usr/bin/python"):
        print("检测到未安装Python，正在安装...")
        os.system("pkg update -y && pkg install python -y")
    
    start_client()

import socket
import threading
import os

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"\nPC > {message}")
        except:
            break

def start_client():
    server_ip = input("输入PC的IP地址: ")
    server_port = 12345
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((server_ip, server_port))
        print(f"已连接到 {server_ip}:{server_port}")
        
        # 启动消息接收线程
        recv_thread = threading.Thread(target=receive_messages, args=(client,))
        recv_thread.daemon = True
        recv_thread.start()
        
        print("输入消息 (输入'exit'退出):")
        while True:
            msg = input("手机 > ")
            if msg.lower() == 'exit':
                break
            client.send(msg.encode('utf-8'))
            
    except Exception as e:
        print(f"连接错误: {e}")
    finally:
        client.close()
        print("连接已关闭")

if __name__ == "__main__":
    # Termux环境设置
    os.system('clear')
    print("Termux聊天客户端")
    start_client()

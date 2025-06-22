import socket
import threading
import sys

def handle_client(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"\n手机 > {message}")
        except:
            break

def start_server(host='0.0.0.0', port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"服务器已启动，监听 {host}:{port}")

    client, addr = server.accept()
    print(f"手机已连接: {addr[0]}:{addr[1]}")
    
    # 启动消息接收线程
    recv_thread = threading.Thread(target=handle_client, args=(client,))
    recv_thread.daemon = True
    recv_thread.start()
    
    try:
        while True:
            msg = input("PC > ")
            if msg.lower() == 'exit':
                break
            client.send(msg.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        server.close()
        print("连接已关闭")

if __name__ == "__main__":
    # 获取本机IP
    host = socket.gethostbyname(socket.gethostname())
    print(f"请在手机上连接此IP: {host}")
    start_server(host)

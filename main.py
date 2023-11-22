import socket
import threading

class ProxyServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(100)
        print(f"Proxy Server listening on {self.host}:{self.port}")

        while True:
            conn, addr = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn,))
            client_thread.start()

    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        first_line = request.split('\n')[0]
        url = first_line.split(' ')[1]

        http_pos = url.find("://")
        if (http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos+3):]

        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos == -1 or webserver_pos < port_pos):
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos+1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        self.forward_request(webserver, port, request, client_socket)

    def forward_request(self, host, port, request, client_socket):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('192.168.0.100', 0))

        server_socket.connect((host, port))
        server_socket.sendall(request.encode())

        while True:
            data = server_socket.recv(4096)
            if len(data) > 0:
                client_socket.send(data)
            else:
                break

        server_socket.close()
        client_socket.close()

if __name__ == '__main__':
    proxy = ProxyServer('0.0.0.0', 2137)
    proxy.start()

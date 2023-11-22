import socket
import threading
import select

class ProxyServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(100)
        print(f"Proxy Server listening on {self.host}:{self.port}")

        while True:
            conn, addr = self.socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn,))
            client_thread.start()

    def handle_client(self, client_socket):
        request = client_socket.recv(1024)
        first_line = request.split(b'\n')[0]
        method, url, protocol = first_line.split()

        if method.upper() == 'CONNECT':
            self.handle_https_connection(client_socket, url)
        else:
            self.handle_http_request(client_socket, request, url)

    def handle_http_request(self, client_socket, request, url):
        http_pos = url.find(b"://")
        if (http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos + 3):]

        port_pos = temp.find(b":")
        webserver_pos = temp.find(b"/")
        if webserver_pos == -1:
            webserver_pos = len(temp)

        webserver = ""
        port = -1
        if (port_pos == -1 or webserver_pos < port_pos):
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]

        self.forward_http_request(webserver, port, request, client_socket)

    def forward_http_request(self, host, port, request, client_socket):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind(('192.168.0.100', 0))

        try:
            server_socket.connect((host, port))
            server_socket.sendall(request.encode())

            while True:
                data = server_socket.recv(4096)
                if len(data) > 0:
                    client_socket.send(data)
                else:
                    break
        except Exception as e:
            print(str(e))

    def handle_https_connection(self, client_socket, url):
        target_host, target_port = url.split(b':')

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('192.168.0.100', 0))

        server_socket.connect((target_host, int(target_port)))
        client_socket.sendall(b'HTTP/1.1 200 Connection established\n\n')

        # Tunelowanie ruchu między klientem a serwerem
        self.tunnel_data(client_socket, server_socket)

    def tunnel_data(self, client_socket, server_socket):
        sockets = [client_socket, server_socket]
        while True:
            read_sockets, write_sockets, error_sockets = select.select(sockets, [], sockets, 0)
            if error_sockets:
                break

            for read_socket in read_sockets:
                other_socket = server_socket if read_socket is client_socket else client_socket
                data = read_socket.recv(4096)
                if not data:
                    break
                other_socket.sendall(data)

        client_socket.close()
        server_socket.close()

if __name__ == '__main__':
    proxy = ProxyServer('0.0.0.0', 2141)
    proxy.start()

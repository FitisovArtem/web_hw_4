import json
import logging
import mimetypes
import socket
import urllib.parse
from datetime import datetime
from pathlib import Path
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_SERVER_HOST = '0.0.0.0'
HTTP_SERVER_PORT = 3000
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class HW4_HTTPRequest(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                other_file = BASE_DIR.joinpath(route.path[1:])
                if other_file.exists():
                    self.send_static(other_file)
                else:
                    self.send_html('error.html', status_code=404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')

        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())

    def do_POST(self):
        data_size = self.headers.get('Content-Length')
        data = self.rfile.read(int(data_size))
        socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_client.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        socket_client.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()


def save_data(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        pars_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        result_data = {str(datetime.now()): pars_dict}

        try:
            with open('storage/data.json', 'r', encoding='utf-8') as file:
                file_data = json.load(file)
            with open('storage/data.json', 'w', encoding='utf-8') as f:
                result_data.update(file_data)
                json.dump(result_data, f, ensure_ascii=False, indent=4)
        except FileNotFoundError:
            with open('storage/data.json', 'w', encoding='utf-8') as except_file:
                json.dump(result_data, except_file, ensure_ascii=False, indent=4)

    except ValueError as e:
        logging.error(e)
    except OSError as e:
        logging.error(e)


def http_server_run(host, port):
    address = (host, port)
    http_server = HTTPServer(address, HW4_HTTPRequest)
    logging.info('HTTP server started')
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    except:
        http_server.server_close()


def socket_server_run(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))
    logging.info('Socked server started')
    try:
        while True:
            message, address = server.recvfrom(BUFFER_SIZE)
            save_data(message)
    except KeyboardInterrupt:
        pass
    finally:
        server.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server_http = Thread(target=http_server_run, args=(HTTP_SERVER_HOST, HTTP_SERVER_PORT))
    server_http.start()

    server_socket = Thread(target=socket_server_run, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()

import socket


FILE = "Wot installer.zip"
HTTP_RESPONSE = b"""HTTP/1.1 200 OK
Content-Type: zip; charset=utf-8
Content-Disposition: attachment; filename="installer.zip
Connection: keep-alive

"""
                

def my_ip():
    """return my current ip in string"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def is_installer_req(request):
    return request.startswith(b"GET") and b"/installer.zip" in request and b"HTTP/1.1\r\n" in request


def main():
    print(f"my ip is: {my_ip()}")
    server = socket.socket()
    server.bind((my_ip(), 50000))
    server.listen(1)
    client, address = server.accept()
    request = client.recv(1024)
    if is_installer_req(request):
        with open(FILE, 'rb') as my_file:
            data = my_file.read()
            client.send(HTTP_RESPONSE + data)
    client.close()


if __name__ == '__main__':
    main()

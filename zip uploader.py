import socket

HTTP_RESPONSE = ""

def my_ip():
    """return my current ip in string"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def main():
    server = socket.socket()
    server.bind((my_ip(), 50000))
    server.listen(1)
    client, address = server.accept()
    x = 4


if __name__ == '__main__':
    main()

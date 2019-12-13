import socket
import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2
STREAM_OUTPUT_PORT = 32000

def voice_stream_connector(enemy_ip):
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        stream_socket.connect((enemy_ip, STREAM_OUTPUT_PORT))
    except socket.error:
        return
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True,
                        output=True, frames_per_buffer=CHUNK)
        while True:
            try:
                data = stream.read(CHUNK)
                stream_socket.send(data)
                stream.write(stream_socket.recv(CHUNK))
            except (IOError, socket.error):
                break
        stream.stop_stream()
        stream.close()
        p.terminate()
    except OSError:
        pass
    stream_socket.close()


def voice_stream_creator(ip):
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        stream_socket.bind((ip, STREAM_OUTPUT_PORT))
        stream_socket.listen(1)
        client, address = stream_socket.accept()
    except socket.error:
        return
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=p.get_format_from_width(WIDTH), channels=CHANNELS,
                        rate=RATE, output=True, input=True, frames_per_buffer=CHUNK)
        while True:
            try:
                data = stream.read(CHUNK)
                client.send(data)
                stream.write(client.recv(CHUNK))
            except (IOError, socket.error):
                break

        stream.stop_stream()
        stream.close()
        p.terminate()
        client.close()
    except OSError:
        pass
    stream_socket.close()


def main():
    ip = input("enter ip address: ")
    print("start")
    voice_stream_creator(ip)


if __name__ == '__main__':
    main()

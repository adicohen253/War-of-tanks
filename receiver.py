import socket
import pyaudio

CHUNK = 1024
CHANNELS = 2
RATE = 44100
WIDTH = 2
HOST = '192.168.1.20'
PORT = 49999


def voice_stream_creator():
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(WIDTH), channels=CHANNELS,
                    rate=RATE, output=True, frames_per_buffer=CHUNK)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    client, address = s.accept()
    print(f"{address[0]} connected")
    while True:
        try:
            stream.write(client.recv(CHUNK))
        except IOError:
            break

    stream.stop_stream()
    stream.close()
    p.terminate()
    client.close()
    s.close()

def main():
    pass

if __name__ == '__main__':
    main()

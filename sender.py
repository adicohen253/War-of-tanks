import socket
import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 40
HOST = "192.168.1.20"
PORT = 49999


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    while True:
        try:
            data = stream.read(CHUNK)
            s.sendall(data)
        except IOError:
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    s.close()


if __name__ == '_main_':
    main()

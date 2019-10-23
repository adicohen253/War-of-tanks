import socket
import pyaudio
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
PORT = 49999


def voice_stream_connector(finish_game):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, PORT))
    p = pyaudio.PyAudio()
    while not finish_game[0]:
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            while not finish_game[0]:
                try:
                    data = stream.read(CHUNK)
                    s.sendall(data)
                    stream.write(data)
                except IOError:
                    break
            stream.stop_stream()
            stream.close()
            p.terminate()
        except OSError:
            time.sleep(3)
    s.close()

def main():
    a = [False]
    voice_stream("", a)
    time.sleep(3)
    a = [True]


if __name__ == '__main__':
    main()

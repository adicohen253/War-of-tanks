import socket
import pyaudio

IP = "192.168.1.20"
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WIDTH = 2
STREAM_OUTPUT_PORT = 32000

def voice_stream_connector(enemy_ip):
    print("connect")
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        stream_socket.connect((enemy_ip, STREAM_OUTPUT_PORT))
    except socket.error:
        return
    p = pyaudio.PyAudio()
    try:
        microphone = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        speaker = p.open(format=p.get_format_from_width(WIDTH),
                         channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        while True:
            try:
                data = microphone.read(CHUNK)
                stream_socket.send(data)
                speaker.write(stream_socket.recv(CHUNK))
            except (IOError, socket.error):
                break
        microphone.stop_stream()
        microphone.close()
        p.terminate()
    except OSError:
        pass
    stream_socket.close()


def voice_stream_creator(ip):
    print("create")
    stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        stream_socket.bind((ip, STREAM_OUTPUT_PORT))
        stream_socket.listen(1)
        client, address = stream_socket.accept()
    except socket.error:
        return
    p = pyaudio.PyAudio()
    try:
        microphone = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        speaker = p.open(format=p.get_format_from_width(WIDTH),
                         channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

        while True:
            try:
                data = microphone.read(CHUNK)
                client.send(data)
                speaker.write(client.recv(CHUNK))
            except (IOError, socket.error):
                break

        microphone.stop_stream()
        microphone.close()
        p.terminate()
        client.close()
    except OSError:
        pass
    stream_socket.close()


def main():
    # voice_stream_creator(IP)
    voice_stream_connector(IP)


if __name__ == '__main__':
    main()

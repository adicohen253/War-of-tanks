FROM python:3.12.3-slim
WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
    mariadb-client \
    libmariadb-dev \
    build-essential \
    xauth \
    tk-dev \
    x11-xserver-utils \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    libwebp-dev

RUN pip install mysql-connector-python pyperclip pygame pandas flask

COPY server.py server_objects.py wot_objects.py RSA.py documentation.txt MapBuilder_icon.png /app/
COPY Maps/ /app/Maps/
COPY ["wot images/Tank.png", "wot images/zone.jpg", "/app/wot images/"]
EXPOSE 5000

CMD ["python", "-u", "server.py"]
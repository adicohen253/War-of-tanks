# will run on djangoweb directory
FROM python:3.12-alpine3.20
RUN apk update && \
    apk add --no-cache mariadb-dev build-base
RUN pip install django mysqlclient

COPY djangoweb/ /app/

WORKDIR /game
RUN apk add wine
RUN wget https://sourceforge.net/projects/nsis/files/NSIS%203/3.06.1/nsis-3.06.1.zip/download -O nsis.zip
RUN unzip nsis.zip
RUN mv nsis-3.06.1 nsis
RUN rm nsis.zip


COPY ["wot.exe", "deployment files/web build/game installer.nsis", "deployment files/web build/start.sh", "/game/"]
COPY ["wot images/", "/game/wot images/"]
COPY ["wot fonts/", "/game/wot fonts/"]
COPY ["wot sounds/", "/game/wot sounds/"]
CMD ["./start.sh"]
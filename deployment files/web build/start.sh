#!/bin/sh
echo -n $SERVER_ADDRESS > serverhost.txt
wine nsis/makensis.exe "game installer.nsis" 2> /dev/null
cd /app && rm /game
sh -c "python manage.py migrate && python manage.py runserver 0.0.0.0:8000 --insecure"
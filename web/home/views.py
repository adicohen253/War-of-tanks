from django.shortcuts import render
from django.http import HttpResponse
from django.utils.encoding import smart_str
from sqlite3 import *


def home(request):
    return render(request, "index.html")


def top_players(request):
    conn = connect("c:/cyber/project/my database.db")
    curs = conn.cursor()
    curs.execute("SELECT * FROM Accounts")
    champions = [{"rank": index + 1, "username": value[0], "wins": value[2],
                  "loses": value[3], "draws": value[4], "total_points": calculate_points(value)}
                 for index, value in enumerate(sorted(curs.fetchall(), key=calculate_points, reverse=True)[:5])]
    return render(request, "champions.html", {"champions": champions})


def calculate_points(account):
    return account[2] + account[4] / 2 - account[3]


def download(request):  # doesn't needed here but must except 1 argument
    with open("c:/cyber/project/Game installer.exe", 'rb') as my_file:
        data = my_file.read()
    resp = HttpResponse(data, content_type='application/force-download')
    resp['Content-Disposition'] = 'attachment; filename=Game installer.exe'
    resp['X-sendfile'] = smart_str("c:/cyber/project/Game.exe")
    return resp

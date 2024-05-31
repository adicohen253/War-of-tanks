from django.shortcuts import render
from django.http import HttpResponse
from django.utils.encoding import smart_str
from .models import Account
from os import path



def home(request):
    return render(request, "index.html")


def top_players(request):
    top5 = Account.objects.all().order_by('-Points')[:5]
    champions = []
    for index in range(len(top5)):
        user = top5[index]
        champions.append({"rank": index + 1, "username": user.Username, "wins": user.Wins, "loses": user.Loses, "draws": user.Draws, "total_points": user.Points})
    return render(request, "champions.html", {"champions": champions})


def download(request):
    with open("Wot Installer.exe", 'rb') as my_file:
        data = my_file.read()
    resp = HttpResponse(data, content_type='application/force-download')
    resp['Content-Disposition'] = 'attachment; filename=Wot installer.exe'
    return resp

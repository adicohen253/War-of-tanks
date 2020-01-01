from django.shortcuts import render
from django.http import HttpResponse
from django.utils.encoding import smart_str


def home(request):
    return render(request, "index.html")


def sign_in(request):
    return render(request, "sign in.html")


def download(request):  # doesn't needed here but must except 1 argument
    with open("c:/cyber/project/Game.exe", 'rb') as my_file:
        data = my_file.read()
    resp = HttpResponse(data, content_type='application/force-download')
    resp['Content-Disposition'] = 'attachment; filename=Game installer.exe'
    resp['X-sendfile'] = smart_str("c:/cyber/project/Game.exe")
    return resp

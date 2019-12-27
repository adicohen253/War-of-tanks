from django.shortcuts import render
# from django.http import HttpResponse


def home(request):
    a = render(request, "index.html")
    return a


def sign_in(request):
    return render(request, "sign in.html")

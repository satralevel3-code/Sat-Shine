from django.shortcuts import render, redirect
from django.http import HttpResponse

def home(request):
    return redirect('login')

def favicon(request):
    return HttpResponse(status=204)

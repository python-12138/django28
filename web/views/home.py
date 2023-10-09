from django.shortcuts import render, HttpResponse, redirect, reverse


def index(request):
    return render(request,'index.html')


def logout(request):
    request.session.flush()
    return  redirect(reverse('web:index'))
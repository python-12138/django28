import datetime

import django
import requests
from django.shortcuts import render, HttpResponse, redirect, reverse
from web.forms.account import RegisterModelForm, SendSmsForm, LoginSMSForm, LoginForm
from django.http import JsonResponse
from web import models
from django.db.models import Q
import uuid
from django.views.decorators.csrf import csrf_exempt


def register(request):
    if request.method == "GET":
        forms = RegisterModelForm()
        return render(request, 'register.html', {"form": forms})

    print(request.POST)
    #

    form = RegisterModelForm(data=request.POST)
    if form.is_valid():
        # 验证通过写入数据库 (密码密文  )
        instance=form.save()
        policy_object = models.PricePolicy.objects.filter(category=1,title='个人免费版').first()

        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=policy_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now()
        )
        return JsonResponse({'status': True, 'data': '/login/'})
    else:
        return JsonResponse({'status': False, "error": form.errors})

#发送短信

def send_sms(request):
    # print(request.GET)
    form = SendSmsForm(request, data=request.GET)
    # form =SendSmsForm(request,data=request.GET)
    # 只是校验手机号:不能为空，格式是正确
    print(form.is_valid())
    if (form.is_valid()):
        return JsonResponse({'status': True})

    return JsonResponse({'status': False, "error": form.errors})

#短信登录
def login_sms(request):
    if request.method == 'GET':
        form = LoginSMSForm()
        return render(request, 'login_sms.html', {"form": form})

    form = LoginSMSForm(request.POST)
    if form.is_valid():
        # 判断验证码是否正确
        mobile_phone = form.cleaned_data['mobile_phone']
        user_object = models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()

        request.session['user_id'] = user_object.id
        request.session['user_name'] = user_object.username
        request.session.set_expiry(60 * 60 * 24 * 14)
        return JsonResponse({"status": True, "data": '/index/'})
    return JsonResponse({"status": False, "error": form.errors})

#用户名密码登录
def login(request):
    '''用户名  密码登录'''
    if request.method == 'GET':
        form = LoginForm(request)
        return render(request, 'login.html', {"form": form})
    form = LoginForm(request, request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        # user_object= models.UserInfo.objects.filter(username=username,password=password).filter()
        user_object = models.UserInfo.objects.filter(Q(email=username) | Q(mobile_phone=username)).filter(
            password=password).first()

        if user_object:
            request.session['user_id'] = user_object.id
            request.session.set_expiry(60*60*24*14)
            return redirect(reverse("web:index"))
        form.add_error('username', '手机号或邮箱或密码错误')

    return render(request, 'login.html', {"form": form})


def image_code(request):

    from io import BytesIO
    from utils.image_code import check_code

    image_object, code = check_code()
    request.session['image_code'] = code
    request.session.set_expiry(60)
    stream = BytesIO()
    image_object.save(stream, 'png')

    return HttpResponse(stream.getvalue())

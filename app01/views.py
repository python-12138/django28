import datetime

from django import forms
from django.core.validators import RegexValidator
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse
from django.utils import timezone
from django_redis import get_redis_connection

from app01 import models
from utils.tencent.sms import send_sms_single


# yapf flake8
# Create your views here.
# 发送短信
def send_sms(request, number):
    pass
    send_sms_single(number, 1930532, )


# modelform 使用样式
class RegisterModelForm(forms.ModelForm):
    mobile_phone = forms.CharField(label='手机号',
                                   validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput())

    confirm_password = forms.CharField(
        label='重复密码',
        widget=forms.PasswordInput())
    code = forms.CharField(
        label='验证码',
        widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)


# 注册
def register(request):
    form = RegisterModelForm()
    return render(request, 'app01/register.html', {'form': form})


def redis_index(request):
    conn = get_redis_connection('default')
    conn.set('nickname', 'wupeiqi', ex=10)
    value = conn.get('nickname')
    print(value)

    return HttpResponse('ok')


def return_test(request):
    result = {
        'success': 0,
        'message': None,
        'url': 'https:baidu.com'
    }

    return JsonResponse(result)


def date_test(request):


    dl = datetime.datetime.now()

    da = timezone.now()

    ds = models.Date_test.objects.filter(name='wu').first()
    dsdate = ds.date

    print(dl, da, dsdate)
    print(timezone.is_aware(dl), timezone.is_aware(da), timezone.is_aware(dsdate))

    context = {
        'dl': dl,
        'da': da,
        'dsdate': dsdate
    }

    return render(request,'timehtml.html',context)


def dictlist(request):

    context={
        'list': ['wupeiqi', '18'],
        'dict':{'name':'wupeiqi','age':18},

        'listdict':[{'name':'wupeiqi','age':18},{'name':'wupeiqi','age':18}]
    }
    return render(request,'dictlist.html',context=context)
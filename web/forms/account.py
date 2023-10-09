from web import models
from django import forms
from django.core.validators import RegexValidator,ValidationError
from django.conf import settings
import random
from django_redis import get_redis_connection
from utils.tencent import sms
from utils import encrypt
from web import models
from web.forms import bootstrap
class RegisterModelForm(bootstrap.BootStrapForm,forms.ModelForm):
    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    password = forms.CharField(
        label='密码',
        min_length=8,
        max_length=16,
        error_messages={
            "min_length":'密码长度不能小于8个字符',
            "max_length":"密码长度不能大于64个字符",
        },
        widget=forms.PasswordInput())

    confirm_password = forms.CharField(
        label='重复密码',
        min_length=8,
        max_length=16,
        error_messages={
            "min_length": '重复密码长度不能小于8个字符',
            "max_length": "重复密码长度不能大于64个字符",
        },
        widget=forms.PasswordInput())
    code = forms.CharField(
        label='验证码',
        widget=forms.TextInput())

    class Meta:
        model = models.UserInfo
        fields = ['username', 'email', 'password', 'confirm_password', 'mobile_phone', 'code',]

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username']
        exists = models.UserInfo.objects.filter(username=username).first()
        if exists:
            raise ValidationError("用户名已经存在")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        exists = models.UserInfo.objects.filter(email=email).first()
        if exists:
            raise ValidationError("email已经存在")
        return email

    def clean_password(self):
        pwd = self.cleaned_data['password']

        return encrypt.md5(pwd)
    def clean_confirm_password(self):
        #pwd = self.cleaned_data['password']
        pwd = self.cleaned_data.get('password')
        confirm_pwd=encrypt.md5(self.cleaned_data['confirm_password'])

        if pwd != confirm_pwd:
            raise ValidationError('密码不一致')
        return confirm_pwd

    def clean_mobile_phone(self):
        moblie_phone = self.cleaned_data['mobile_phone']
        exists=models.UserInfo.objects.filter(mobile_phone=moblie_phone).exists()
        if exists:
            raise  ValidationError('手机号已经注册')
        return moblie_phone

    def clean_code(self):
        code = self.cleaned_data['code']

        #mobile_phone=self.cleaned_data['mobile_phone']
        #取别的字段用get避免程序终止抛出异常
        mobile_phone = self.cleaned_data.get('mobile_phone')
        if not mobile_phone:
            return code
        print(type(mobile_phone))
        conn =get_redis_connection()
        redis_code=conn.get(mobile_phone)
        if not redis_code:
            raise ('验证码失效或未发送，重新发送')

        str_code=redis_code.decode('utf-8')
        if code.strip() != str_code:
            raise ValidationError('验证码失效或者验证码书写错误')

        return code




class SendSmsForm(forms.Form):

    mobile_phone = forms.CharField(label='手机号',validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ],)
    def __init__(self,request,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.request=request

    def clean_mobile_phone(self):
        #手机号校验的狗子
        mobile_phone=self.cleaned_data['mobile_phone']

        #判断短信模板是否有问题
        tpl=self.request.GET.get('tpl')

        templete_id=settings.TENCENT_SMS_TEMPLATE.get(tpl)
        if not templete_id:
            raise ValidationError('短信模板错误')
        #校验数据库中是否已经有手机号
        exists=models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        if tpl=='login':
            if not exists:
                raise ValidationError('手机号不存在存在')
        else:
            if exists:
                raise ValidationError("手机号已经存在")

        # 发短信 &  写 redis
        code = random.randrange(1000,9999)

        code=1111
        #短信发不出去 修改为固定值 1111
        #result=sms.send_sms_single(mobile_phone,templete_id,[code,])
        result= {'result': 0, 'errmsg': "发送成功"}
        if result['result'] != 0:
            raise ValidationError(result['errmsg'])

        conn =get_redis_connection()
        conn.set(mobile_phone,code,ex=60)

        return mobile_phone


class LoginSMSForm(bootstrap.BootStrapForm,forms.Form):

    mobile_phone = forms.CharField(label='手机号', validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误'), ])
    code = forms.CharField(
        label='验证码',
        widget=forms.TextInput())


    def clean_mobile_phone(self):
        mobile_phone=self.cleaned_data.get('mobile_phone')
        exists= models.UserInfo.objects.filter(mobile_phone=mobile_phone).first()
        if not exists:
            raise ValidationError('手机号不存在')

        return mobile_phone

    def clean_code(self):
        code=self.cleaned_data['code']
        mobile_phone = self.cleaned_data.get('mobile_phone')
        #手机号不存在无需校验
        if not mobile_phone:
            return code

        conn=get_redis_connection()
        redis_code = conn.get(mobile_phone)
        str_code = redis_code.decode('utf-8')
        if code.strip() != str_code:
            raise ValidationError('验证码错误')

        return code


class LoginForm(bootstrap.BootStrapForm,forms.Form):
    username=forms.CharField(label="邮箱或者手机号")
    password=forms.CharField(label="密码",widget=forms.PasswordInput(render_value=True))
    code=forms.CharField(label="验证码")

    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.request=request

    def clean_password(self):
        pwd = self.cleaned_data['password']
        return encrypt.md5(pwd)
    def clean_code(self):
        '''验证图片验证码是否正确'''

        code = self.cleaned_data['code']

        session_code = self.request.session.get('image_code')

        if not session_code:
            raise  ValidationError('验证码过期')
        if code.strip().upper() != session_code.upper() :
            raise ValidationError('验证码输入错误')

        return code

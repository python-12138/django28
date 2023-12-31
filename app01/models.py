from django.db import models

# Create your models here.
class UserInfo(models.Model):
    username=models.CharField(verbose_name='用户名',max_length=32)
    email=models.EmailField(verbose_name='邮箱',max_length=32,null=True)
    phone=models.CharField(verbose_name='手机号',max_length=32,null=True)
    pw=models.CharField(verbose_name='密码',max_length=32,null=True)


class Date_test(models.Model):
    name = models.CharField(verbose_name='名字',max_length=32)
    date=models.DateTimeField(verbose_name='日期',auto_now_add=True)


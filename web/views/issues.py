from django.shortcuts import render,redirect,reverse
from utils.tencent.cos import delete_bucket
from web import models



def issues(request,project_id):
    return render(request,'issues.html')
from django.shortcuts import redirect,render,reverse
from django.http import HttpResponse,JsonResponse



def statistics(request,project_id):

    return render(request,'statistics.html')



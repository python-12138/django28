from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.


def render_ajax(request):
    if request.method =='GET':
        return render(request,'ajax.html')

    print(request.POST.get('username'))
    print(request.GET.get('a'))

    return render(request,'ajax.html')
def ajax_hello(request):

    return JsonResponse({"text":"hello world"})
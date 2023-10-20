import collections
import time
from datetime import timedelta

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from web import models


def dashboard(request, project_id):
    '''概览
        问题数据处理
    '''
    # print(models.Issues.objects.filter(project_id=project_id ).values('status'))
    # print(models.Issues.objects.filter(project_id=project_id ).values_list('status'))
    # 对于python 3.6 之前的字典是无序字典 需要使用  collections.OrderedDict() 让他成为有序字典
    status_dict = collections.OrderedDict()

    for key, value in models.Issues.status_choices:
        status_dict[key] = {'text': value, 'count': 0}

    issues_data = models.Issues.objects.filter(project_id=project_id, ).values('status').annotate(ct=Count('status'))

    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']

    # 用户列表
    user_list = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username')

    # 获取前十个问题、已经指派的问题
    top_ten = models.Issues.objects.filter(project_id=project_id, assign__isnull=False).order_by('-id')[:10]

    context = {
        'status_dict': status_dict,
        'user_list': user_list,
        'top_ten_object': top_ten,
    }
    # print(status_dict)

    print(1111,status_dict)

    return render(request, 'dashboard.html', context)


def issueschart(request, project_id):
    '''在概览界面生成highchats图片所需的数据
    '''
    # 最近三十天、每天创建的问题数量，用timezone

    today = timezone.datetime.date(timezone.now())

    # 有序字典

    date_dict = collections.OrderedDict()

    for i in range(30):
        date = today - timedelta(days=i)
        date_dict[date.strftime('%Y-%m-%d')] = [time.mktime(date.timetuple()) * 1000, 0]

    result = models.Issues.objects.filter(project_id=project_id,
                                          create_datetime__gte=timezone.now() - timedelta(days=30)).extra(
        select={'ctime': "strftime('%%Y-%%m-%%d',create_datetime)"}).values('ctime').annotate(ct=Count('id')).values(
        'ctime', 'ct')

    for item in result:
        date_dict[item['ctime']][1] = item['ct']


    #print(1111,list(date_dict.values()))


    return JsonResponse({'status': True, 'data': list(date_dict.values())})

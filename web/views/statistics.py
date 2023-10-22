import collections
from copy import deepcopy

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from web import models


def statistics(request, project_id):
    return render(request, 'statistics.html')


def statistics_priority(request, project_id):
    '''按照优先级生成饼图'''
    # 找到所有的问题，根据优先级分组，每个优先级的问题数量
    # 将每个优先级的问题数量转换成饼图数据

    start = request.GET.get('start')
    end = request.GET.get('end')

    # 1.构造字典
    # {'danger':{name:'' ,y::0},'warning':{name:'' ,y::0} }
    data_list = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_list[key] = {'name': text, 'y': 0}

    # queryset 内的数据是一个一个字典组成，组成了queryset类型<QuerySet [{'priority': 'danger', 'ct': 4}, {'priority': 'warning', 'ct': 1}]>
    # user = models.UserInfo.objects.all().values()

    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))

    for item in result:
        data_list[item['priority']]['y'] = item['ct']
    # print(list(data_list.values()))
    return JsonResponse({'status': True, 'message': 'ok', 'data': list(data_list.values())})


def statistics_projectuser(request, project_id):
    '''项目成员每个人被分配的任务数量（问题类型的配比）'''

    # 找到所有的问题并且根据指派的用户分组
    # 用户数据格式
    user_info = {
        'username': None,
        'status': {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0,
        }
    }
    # 声明有序列表
    all_user_info = collections.OrderedDict()
    # 取出起始日期 以及 结束日期
    start = request.GET.get('start')
    end = request.GET.get('end')
    # print(start,end)
    all_assign_user = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                                   create_datetime__lt=end).values('assign__id', 'assign__username',
                                                                                   'status').annotate(ct=Count('id'))

    '''categories  = list(set([str(item['assign__id']) + item['assign__username'] for item in all_assign_user if
                      item['assign__username'] is not None]))'''

    user_dict = {item['assign__id']: item['assign__username'] for item in all_assign_user}

    categories = []
    # 对取到的每一个问题以及相关的用户初始化数据
    for key, value in user_dict.items():
        # 添加对应的 前端图标的 x 轴的数据
        categories.append(value)
        if value is None:
            user_info['username'] = value
        else:
            user_info['username'] = str(key) + value
        # 字典是可变的，所以要用copy()方法，python是指向型变量，不用copy修改内容的话会像指针一样修改掉指向的值,浅拷贝值拷贝
        all_user_info[key] = deepcopy(user_info)

    # 对每一个问题进行设置对应的问题的值，没有指派用户的问题设置为None
    for item in all_assign_user:
        all_user_info[item['assign__id']]['status'][item['status']] = item['ct']

    # print(categories)
    # print(all_user_info)

    data_result_dict = {
        1: {'name': '新建', 'data': []},
        2: {'name': '处理中', 'data': []},
        3: {'name': '已解决', 'data': []},
        4: {'name': '已忽略', 'data': []},
        5: {'name': '待反馈', 'data': []},
        6: {'name': '已关闭', 'data': []},
        7: {'name': '重新打开', 'data': []},
    }
    # 处理数据符合前端图标的数据格式 前端接受的数据是 int

    for key, use_data in all_user_info.items():
        for index, value in data_result_dict.items():
            value['data'].append(use_data['status'][index])

    if None in categories:
        index = categories.index(None)
        categories[index] = '未指派'

    context = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        }
    }

    return JsonResponse(context)

import time
from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect, reverse
from web import models
from web.forms.project import ProjectModelForm
from utils.tencent.cos import create_bucket

def project_list(request):
    '项目列表'

    if request.method == 'GET':
        '''
        1.丛数据库中获取俩部分数据
             我创建的所有项目 ： 已星标、未星标
             我参数的所有项目：已星标、未星标
        2. 提取已星标
        列表  = 循环 （我创建的所有项目） + （我参与的所有项目） 把已星标的数据提取
        得到三个列表:星标、创建、参与
        '''
        project_dict = {'star': [], 'my': [], 'join': []}

        my_project_list = models.Project.objects.filter(creator=request.tracer.user)
        for row in my_project_list:
            if row.star:
                project_dict['star'].append({"value":row,"type":"my"})
            else:
                project_dict['my'].append(row)
        join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
        for item in join_project_list:
            if item.star:
                project_dict['star'].append({"value":item.project,"type":"join"})
            else:
                project_dict['join'].append(item.project)

        form = ProjectModelForm(request)
        return render(request, 'project_list.html', {"form": form, "project_dict": project_dict})
    form = ProjectModelForm(request, request.POST)
    #验证通过创建项目
    if form.is_valid():

        bucket = "{}-{}-1304077854".format(request.tracer.user.mobile_phone,str(int(time.time())))
        region = 'ap-nanjing'
        create_bucket(bucket=bucket,region=region)
        form.instance.bucket=bucket
        form.instance.region=region

        form.instance.creator = request.tracer.user

        instance=form.save()
        #创建每个项目默认的问题类型
        issues_type_project_list = []
        for item in models.IssuesType.PROJECT_INIT_LIST:
            issues_type_project_list.append(models.IssuesType(project=instance,title=item))

        models.IssuesType.objects.bulk_create(issues_type_project_list)

        return JsonResponse({'status': True})

    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request, project_type, project_id):
    '''星标项目'''

    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)

        #models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)
        return redirect(reverse('web:project_list'))
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=True)
        return redirect(reverse('web:project_list'))

    return HttpResponse('请求错误')


def project_unstar(request,project_type, project_id):

    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=False)

        # models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)
        return redirect(reverse('web:project_list'))
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=False)
        return redirect(reverse('web:project_list'))

    return HttpResponse('请求错误')

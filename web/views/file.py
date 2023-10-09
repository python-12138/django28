import json
from django.http import JsonResponse,HttpResponse
from django.shortcuts import render,reverse
from django.views.decorators.csrf import csrf_exempt

from utils.tencent.cos import delete_file, delete_file_list, credential
from web import models
from web.forms.file import FileFolderModelForm,FileModelForm


def file(request, project_id):
    '''文件列表 &添加文件夹、'''
    parent_object = None
    folder_id = request.GET.get('folder', "")
    if folder_id.isdecimal():
        parent_object = models.FileRepository.objects.filter(id=folder_id, file_type=2,
                                                             project=request.tracer.project).first()

    # get 查看页面
    if request.method == 'GET':
        breadcrumb_list = []
        parent = parent_object
        while parent:
            breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent
        queryset = models.FileRepository.objects.filter(project=request.tracer.project)

        if parent_object:
            file_object = queryset.filter(parent=parent_object).order_by('-file_type')
        else:
            file_object = queryset.filter(parent__isnull=True).order_by('-file_type')
        form = FileFolderModelForm(request, None)
        context = {
            'from': form,
            'file_object': file_object,
            'breadcrumb_list': breadcrumb_list,
            'folder_object': parent_object,
        }
        return render(request, 'file.html', context)

    # POST添加文件夹 &  修改文件夹
    fid = request.POST.get('fid', '')
    edit_object = None

    if fid.isdecimal():
        edit_object = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                           project=request.tracer.project).first()

    if edit_object:
        form = FileFolderModelForm(request, parent_object, request.POST, instance=edit_object)
    else:
        form = FileFolderModelForm(request, parent_object, request.POST)

    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.file_type = 2
        form.instance.update_user = request.tracer.user
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'status': True, })

    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):

    fid = request.GET.get('fid')

    delete_object = models.FileRepository.objects.filter(id=fid, project=request.tracer.project).first()

    if delete_object.file_type == 1:
        # 删除文件返还当前项目已经使用的空间
        request.tracer.project.use_space -= delete_object.file_size
        request.tracer.project.save()

        # cos  删除文件
        delete_file(request.tracer.project.bucket, request.tracer.project.region, delete_object.key)

        delete_object.delete()
        return JsonResponse({'status': True})

    total_size = 0
    key_list = []

    folder_list = [delete_object]

    for folder in folder_list:
        child_list = models.FileRepository.objects.filter(parent=folder, project=request.tracer.project).order_by(
            '-file_type')

        for child in child_list:
            if child.file_type == 2:
                folder_list.append(child)
            else:
                # 文件总和
                total_size += child.file_size
                # 删除文件
                key_list.append({"key": child.key})

    # 删除文件
    if key_list:
        delete_file_list(request.tracer.project.bucket, request.tracer.project.region, key_list)

    if total_size:
        request.tracer.project.use_space -= total_size
        request.tracer.project.save()

    # 级联删除文件夹
    delete_object.delete()
    return JsonResponse({'status': True})


@csrf_exempt
def cos_credential(request, project_id):
    per_file_limit = request.tracer.price_policy.per_file_size * 1024 * 1024
    total_file_limit = request.tracer.price_policy.project_space * 1024 * 1024 * 1024

    total_size = 0
    file_list = json.loads(request.body.decode('utf-8'))

    for item in file_list:
        # 文件的字节大小 item['size'] = B
        # 单文件限制的大小 M
        # 超出限制
        if item['size'] > per_file_limit:
            msg = "单文件超出限制（最大{}M），文件：{}，请升级套餐。".format(request.tracer.price_policy.per_file_size,
                                                                       item['name'])
            return JsonResponse({'status': False, 'error': msg})
        total_size += item['size']
    # 总容量进行限制
    # request.tracer.price_policy.project_space  # 项目的允许的空间
    # request.tracer.project.use_space # 项目已使用的空间
    if request.tracer.project.use_space + total_size > total_file_limit:
        return JsonResponse({'status': False, 'error': "容量超过限制，请升级套餐。"})
    data_dict = credential(request.tracer.project.bucket, request.tracer.project.region)
    print(data_dict)

    return JsonResponse({'status': True, 'data': data_dict})


@csrf_exempt
def file_post(request, project_id):
    """ 已上传成功的文件写入到数据 """
    """
    name: fileName,
    key: key,
    file_size: fileSize,
    parent: CURRENT_FOLDER_ID,
    # etag: data.ETag,
    file_path: data.Location
    """

    print(request.POST)
    # 把获取到的数据写入数据库即可
    form = FileModelForm(request,data=request.POST)

    print(1)

    if form.is_valid():
        print(2)
        # 通过ModelForm.save存储到数据库中的数据返回的isntance对象，无法通过get_xx_display获取choice的中文
        # form.instance.file_type = 1
        # form.update_user = request.tracer.user
        # instance = form.save() # 添加成功之后，获取到新添加的那个对象（instance.id,instance.name,instance.file_type,instace.get_file_type_display()

        # 校验通过：数据写入到数据库
        data_dict = form.cleaned_data
        print(type(data_dict))
        data_dict.pop('etag')
        data_dict.update({'project': request.tracer.project, 'file_type': 1, 'update_user': request.tracer.user})
        print(3)
        instance = models.FileRepository.objects.create(**data_dict)
        print(4)
        # 项目的已使用空间：更新 (data_dict['file_size'])
        request.tracer.project.use_space += data_dict['file_size']
        request.tracer.project.save()

        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.update_user.username,
            'datetime': instance.update_datetime,
            'download_url': reverse('file_download', kwargs={"project_id": project_id, 'file_id': instance.id})
            # 'file_type': instance.get_file_type_display()
        }
        return JsonResponse({'status': True, 'data': result})
    print(form.errors)
    return JsonResponse({'status': False, 'data': "文件错误"})


def file_download(request,project_id,file_id):
    '''下载文件'''
    #文件内容
    #响应头
    #打开文件获取文件内容 本项目内容才cos 云存储内

    import requests

    file_object = models.FileRepository.objects.filter(id=file_id,project_id=project_id).first()

    print(file_object.file_path)
    res =requests.get(url= 'https://'+file_object.file_path)
    data = res.content


    response = HttpResponse(data)
    # 设置content_type=application/octet-stream 用于提示下载框
    #response = HttpResponse(data, content_type="application/octet-stream")


    response['Content-Disposition'] = 'attachment; filename={}'.format(file_object.name)

    return response
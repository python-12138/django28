from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.views.decorators.csrf import csrf_exempt

from utils.encrypt import uid
from utils.tencent.cos import upload_file
from web import models
from web.forms.wiki import WikiModelForm


def wiki(request, project_id):
    '''wiki的首页展示'''
    wiki_id = request.GET.get('wiki_id')
    if wiki_id is None or not wiki_id.isdecimal():
        return render(request, 'wiki.html')

    wiki_object = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    print(wiki_object)
    return render(request, 'wiki.html', {'wiki_object': wiki_object})


def wiki_add(request, project_id):
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'wiki_form.html', {'form': form})
    form = WikiModelForm(request, request.POST)
    if form.is_valid():

        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))
    return render(request, 'wiki_form.html', {'form': form})


# wiki目录
def wiki_catalog(request, project_id):
    # data = models.Wiki.objects.filter(project_id = project_id).values_list('id','title','parent_id')
    data = models.Wiki.objects.filter(project_id=project_id).values('id', 'title', 'parent_id').order_by('depth', 'id')

    return JsonResponse({"status": True, 'data': list(data)})


# wiki文档细节'''
def wiki_detail(request, project_id):
    return HttpResponse('okl')
    return render()


def delete(request, project_id, wiki_id):
    '''删除wiki文档'''
    models.Wiki.objects.filter(project_id=project_id, id=wiki_id).delete()

    return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))


# wiki_edit
def edit(request, project_id, wiki_id):
    wiki_object = models.Wiki.objects.filter(project_id=project_id, id=wiki_id).first()

    if not wiki_object:
        return redirect(reverse('web:wiki', kwargs={'project_id': project_id}))

    if request.method == 'GET':
        form = WikiModelForm(request, instance=wiki_object)
        return render(request, 'wiki_form.html', {'form': form})

    form = WikiModelForm(request, request.POST, instance=wiki_object)
    print(form)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()

        url = reverse('web:wiki', kwargs={'project_id': project_id})
        # url=url+ '?wiki_id=' + wiki_id
        preview_url = "{0}?wiki_id={1}".format(url, wiki_id)
        return redirect(preview_url)

    return render(request, 'wiki_form.html', {'form': form})


@csrf_exempt
def wiki_upload(request, project_id):

    result = {
        'success': 0,
        'message': None,
        'url': None
    }

    image_object = request.FILES.get('editormd-image-file')
    print(image_object.name,image_object.size)
    print(type(image_object))

    #return JsonResponse(result)

    if not image_object:
        result['message'] = "文件不存在"
        return JsonResponse(result)

    ext = image_object.name.rsplit('.')[-1]
    key = "{}.{}".format(uid(request.tracer.user.mobile_phone), ext)
    image_url = upload_file(
        request.tracer.project.bucket,
        request.tracer.project.region,
        image_object,
        key
    )
    result['success'] = 1
    result['url'] = image_url


    return JsonResponse(result)

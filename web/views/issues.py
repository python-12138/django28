import json

from django.http import JsonResponse
from django.shortcuts import render, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from utils.encrypt import uid
from utils.pagination import Pagination
from web import models
from web.forms.issues import IssuesModelForm, IssuesReplayModelForm, InviteModelForm
import datetime

class CheckFilter(object):
    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        # 对每一个checkbox生成html代码，对于已经checked 的选项要将其href内的对应的参数去掉才能生成对应的可以取消的checkbox

        for item in self.data_list:
            key = str(item[0])
            text = item[1]
            ck = ''
            value_list = self.request.GET.getlist(self.name)
            # 如果对应的key在对应的列表内则加上key
            if key in value_list:
                ck = 'checked'
                value_list.remove(key)
            else:
                value_list.append(key)

            # print(value_list)
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            if 'page' in query_dict:
                # query_dict.pop('page')
                del query_dict['page']
            # print(query_dict)

            param_url = query_dict.urlencode()
            if param_url:
                url = "{}?{}".format(self.request.path_info, query_dict.urlencode())
            else:
                url = self.request.path_info

            tpl = '<a class="cell" href="{url}"><input type="checkbox" {ck} /><label>{text}</label></a>'
            html = tpl.format(url=url, ck=ck, text=text)

            yield mark_safe(html)


class SelectFilter(object):

    def __init__(self, name, data_list, request):
        self.name = name
        self.data_list = data_list
        self.request = request

    def __iter__(self):
        yield mark_safe(
            '<select class="select2"  multiple="multiple" data-placeholder="Choose a state" style="width:100%;">')
        for item in self.data_list:
            key = str(item[0])
            text = item[1]

            selected = ""
            value_list = self.request.GET.getlist(self.name)
            if key in value_list:
                selected = "selected"
                value_list.remove(key)
            else:
                value_list.append(key)

                # print(value_list)
            query_dict = self.request.GET.copy()
            query_dict._mutable = True
            query_dict.setlist(self.name, value_list)

            if 'page' in query_dict:
                # query_dict.pop('page')
                del query_dict['page']
            # print(query_dict)

            param_url = query_dict.urlencode()
            if param_url:
                url = "{}?{}".format(self.request.path_info, param_url)
            else:
                url = self.request.path_info

            html = '<option value="{url}" {selected}>{text}</option>'.format(url=url, selected=selected, text=text)

            yield mark_safe(html)

        yield mark_safe('</select>')


def is_filter(self):
    self.filter_dict = {}
    name = self.request.GET.get('name')
    value = self.request.GET.get('value')
    if name and value:
        self.filter_dict[name] = value
    return self.filter_dict


def issues(request, project_id):
    if request.method == 'GET':

        allow_filter_name = ['status', 'issues_type', 'priority', 'assign', 'attention']
        condition = {}
        for name in allow_filter_name:
            value_list = request.GET.getlist(name)
            if not value_list:
                continue
            condition["{}__in".format(name)] = value_list

        # 分页获取数据
        queryset = models.Issues.objects.filter(project_id=project_id).filter(**condition)

        page_object = Pagination(current_page=request.GET.get('page'),
                                 all_count=queryset.count(),
                                 base_url=request.path_info,
                                 query_params=request.GET,
                                 per_page=5
                                 )
        issues_object_list = queryset[page_object.start:page_object.end]
        form = IssuesModelForm(request)

        project_issues_type = models.IssuesType.objects.filter(project_id=project_id).values_list('id', 'title')

        project_total_user = [(request.tracer.project.creator_id, request.tracer.project.creator.username)]
        join_user = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__username')
        project_total_user.extend(join_user)

        invite_form = InviteModelForm()
        context = {
            'form': form,
            'invite_form': invite_form,
            'issues_object_list': issues_object_list,
            'page_html': page_object.page_html(),
            'filter_list': [
                {'title': '问题类型', 'filter': CheckFilter('issues_type', project_issues_type, request)},
                {'title': '优先级', 'filter': CheckFilter('priority', models.Issues.priority_choices, request)},
                {'title': '状态', 'filter': CheckFilter('status', models.Issues.status_choices, request)},
                {'title': '指派者', 'filter': SelectFilter('assign', project_total_user, request)},
                {'title': '关注着', 'filter': SelectFilter('attention', project_total_user, request)},

            ],

        }

        return render(request, 'issues.html', context)

    form = IssuesModelForm(request, data=request.POST)
    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.creator = request.tracer.user
        form.save()
        return JsonResponse({'status': True, })
    return JsonResponse({'status': False, 'error': form.errors})


def issues_detail(request, project_id, issues_id):
    issues_object = models.Issues.objects.filter(id=issues_id, project_id=project_id).first()
    form = IssuesModelForm(request, instance=issues_object)
    return render(request, 'issues_detail.html', {'form': form, 'issues_object': issues_object})


@csrf_exempt
def issues_record(request, project_id, issues_id):
    """ 初始化操作记录 """
    '''应该先判断是否可以评论是否可以操作'''
    if request.method == 'GET':

        # 初始化操作记录
        reply_list = models.IssuesReply.objects.filter(issues_id=issues_id, issues__project_id=project_id)
        # queryset转换为set
        data_list = []
        for row in reply_list:
            data = {
                'id': row.id,
                'reply_type_text': row.get_reply_type_display(),
                'content': row.content,
                'creator': row.creator.username,
                'datetime': row.create_datetime.strftime("%Y-%m-%d %H:%M"),
                'parent_id': row.reply_id,
            }
            data_list.append(data)

        return JsonResponse({'status': True, 'data': data_list})

    form = IssuesReplayModelForm(data=request.POST)

    if form.is_valid():
        form.instance.issues_id = issues_id
        form.instance.reply_type = 2
        form.instance.creator = request.tracer.user
        instance = form.save()

        info = {
            'id': instance.id,
            'reply_type_text': instance.get_reply_type_display(),
            'content': instance.content,
            'creator': instance.creator.username,
            'datetime': instance.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': instance.reply_id,
        }
        return JsonResponse({'status': True, 'data': info})

    # 返回一个JsonResponse对象，其中包含一个字典，字典中包含一个状态码'status'，以及一个错误信息'error'，错误信息由表单form.errors获取
    return JsonResponse({'status': False, 'error': form.errors})


@csrf_exempt
def issues_change(request, project_id, issues_id):
    post_dict = json.loads(request.body.decode('utf-8'))
    issues_object = models.Issues.objects.filter(id=issues_id, project_id=project_id).first()

    name = post_dict.get('name')
    value = post_dict.get('value')

    # 可以得到当前字段的各个属性
    field_object = models.Issues._meta.get_field(name)

    def create_reply_record(content):
        new_object = models.IssuesReply.objects.create(
            reply_type=1,
            issues=issues_object,
            content=content,
            creator=request.tracer.user,
        )
        new_reply_dict = {
            'id': new_object.id,
            'reply_type_text': new_object.get_reply_type_display(),
            'content': new_object.content,
            'creator': new_object.creator.username,
            'datetime': new_object.create_datetime.strftime("%Y-%m-%d %H:%M"),
            'parent_id': new_object.reply_id,

        }

        return new_reply_dict

    # 1.数据库字段更新
    # 1.1 文本
    if name in ['subject', 'desc', 'start_date', 'end_date']:
        if not value:
            if not field_object.null:
                return JsonResponse({'status': False, 'error': '%s字段不能为空' % name})
            setattr(issues_object, name, None)
            issues_object.save()
            change_record = "{}更新为空".format(field_object.verbose_name)
        else:
            setattr(issues_object, name, value)
            issues_object.save()
            change_record = "{}更新为{}".format(field_object.verbose_name, value)

        return JsonResponse({'status': True, 'new_reply_dict': create_reply_record(change_record)})

    # # 1.2 FK字段

    if name in ['module', 'issues_type', 'parent', 'assign']:
        # 选择为空
        if not value:
            # 字段不允许为空
            if not field_object.null:
                return JsonResponse({'status': False, 'error': '%s字段不能为空' % name})
            # 字段允许为空
            setattr(issues_object, name, None)
            issues_object.save()
            change_record = "{}更新为空".format(field_object.verbose_name)
        else:
            # 选择不为空
            if name == 'assign':
                # 是否是项目的创建者、是否是项目的参与者
                if value == str(request.tracer.project.creator.id):
                    instance = request.tracer.project.creator
                else:
                    project_user_object = models.ProjectUser.objects.filter(project_id=project_id,
                                                                            user_id=value).first()
                    if project_user_object:
                        instance = project_user_object.user
                    else:
                        instance = None
                    if not instance:
                        return JsonResponse({'status': False, 'error': '选择的值不存在'})
                setattr(issues_object, name, instance)
                issues_object.save()
                change_record = "{}更新为{}".format(field_object.verbose_name, str(instance))
            else:
                # 条件判断：用户输入的值，是自己的值
                instance = field_object.remote_field.model.objects.filter(id=value, project_id=project_id).first()
                if not instance:
                    return JsonResponse({'status': False, 'error': '%s字段不存在' % name})
                setattr(issues_object, name, instance)
                issues_object.save()
                change_record = "{}更新为{}".format(field_object.verbose_name, str(instance))

        return JsonResponse({'status': True, 'new_reply_dict': create_reply_record(change_record)})
    # 1.3 choice字段
    if name in ['priority', 'status', 'mode']:
        select_text = None
        for key, text in field_object.choices:
            if str(key) == value:
                select_text = text
        if not select_text:
            return JsonResponse({'status': False, 'error': '选择的字段值不存在'})

        setattr(issues_object, name, value)
        issues_object.save()
        change_record = "{}更新为{}".format(field_object.verbose_name, select_text)
        return JsonResponse({'status': True, 'new_reply_dict': create_reply_record(change_record)})

    # 1.4 M2M字段
    if name == 'attention':
        # 1.4 M2M字段
        # 1.4.1 先获取到原来的关注者列表
        if not isinstance(value, list):
            return JsonResponse({'status': False, 'error': '数据格式错误'})

        if not value:
            issues_object.attention.set(value)
            issues_object.save()
            change_record = "{}更新为空".format(field_object.verbose_name)
        else:
            # 获取当前项目的所有成员
            user_dict = {str(request.tracer.project.creator.id): request.tracer.project.creator.username}
            project_user_list = models.ProjectUser.objects.filter(project_id=project_id)
            for item in project_user_list:
                user_dict[str(item.user_id)] = item.user.username

            username_list = []
            for user_id in value:
                username = user_dict.get(str(user_id))
                if not username:
                    return JsonResponse({'status': False, 'error': '选择的用户不存在,刷新或重新设置'})

                username_list.append(username)

            issues_object.attention.set(value)
            issues_object.save()
            change_record = "{}更新为{}".format(field_object.verbose_name, ",".join(username_list))

        return JsonResponse({'status': True, 'new_reply_dict': create_reply_record(change_record)})

    return JsonResponse({'status': False, 'error': '参数错误'})


def invite_url(request, project_id):
    '''生成邀请码'''
    form = InviteModelForm(request.POST)
    if form.is_valid():
        '''1.创建随机的邀请码
            2.验证码保存到数据库
            3.限制：只有创建者才能邀请
        '''
        if request.tracer.user != request.tracer.project.creator:
            form.add_error('period', '只有项目创建者才能邀请')
            return JsonResponse({'status': False, 'error': form.errors})
        random_invite_code = uid(request.tracer.user.mobile_phone)
        form.instance.project = request.tracer.project
        form.instance.code = random_invite_code
        form.instance.creator = request.tracer.user

        form.save()

        url_path = reverse('web:invite_join', kwargs={'code': random_invite_code})
        print(url_path)

        url = "{}://{}{}".format(request.scheme, request.get_host(), url_path)

        return JsonResponse({'status': True, 'data': url})

    return JsonResponse({'status': False, 'error': form.errors})


def invite_join(request, code):
    '''访问邀请码'''
    print(1)


    current_datetime = timezone.now()

    invite_object = models.ProjectInvite.objects.filter(code=code).first()
    if not invite_object:
        return render(request, 'invite_join.html', {'error': '邀请码不存在'})
    print(2)
    if invite_object.project.creator == request.tracer.user:
        return render(request, 'invite_join.html', {'error': '创建者无需加入'})
    print(3)
    exists = models.ProjectUser.objects.filter(project=invite_object.project, user=request.tracer.user).exists()
    if exists:
        return render(request, 'invite_join.html', {'error': '已经加入项目无需重复加入'})

    # 最多允许的成员 （要进入的项目的的创建者的限制）
    # max_member=request.tracer.price_policy.project_member
    max_member = invite_object.project.creator

    max_transaction = models.Transaction.objects.filter(user=invite_object.project.creator, status=2).order_by(
        '-id').first()
    print(max_transaction.price_policy.category)
    if max_transaction.price_policy.category ==  1:
        max_member = max_transaction.price_policy.project_member
    else:
        if max_transaction.end_datetime < current_datetime:
            free_object = models.PricePolicy.objects.filter(category='1', title='免费版').first()
            max_member = free_object.project_member
        else:
            max_member = max_transaction.price_policy.project_member

    # 目前所有成员
    current_member = models.ProjectUser.objects.filter(project=invite_object.project).count()
    current_member += 1
    print(4)

    if current_member > max_member:
        return render(request, 'invite_join.html', {'error': '项目成员已满，通知创建者购买套餐'})

    # 邀请码是否过期

    limit_datetime = invite_object.create_datetime + timezone.timedelta(minutes=invite_object.period)

    print(5)
    if current_datetime > limit_datetime:
        return render(request, 'invite_join.html', {'error': '邀请码已过期'})

    print(6)
    if invite_object.count:
        if invite_object.use_count >= invite_object.count:
            return render(request, 'invite_join.html', {'error': '邀请码已用完'})
        invite_object.use_count += 1
        invite_object.save()
    print(7)
    models.ProjectUser.objects.create(user=request.tracer.user, project=invite_object.project)
    print(8)
    invite_object.project.join_count += 1
    invite_object.project.save()
    return render(request, 'invite_join.html', {'project': invite_object.project})

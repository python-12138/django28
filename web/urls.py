from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, re_path

from web.views import account, project, manage, wiki, file, viewsetting,issues
from web.views import home

urlpatterns = [

                  re_path(r'^register/$', account.register, name='register'),
                  re_path(r'^send/sms/$', account.send_sms, name='send_sms'),
                  re_path(r'^login/sms/$', account.login_sms, name='login_sms'),
                  re_path(r'^login/$', account.login, name='login'),
                  re_path(r'^image/code/$', account.image_code, name='image_code'),
                  re_path(r'^index/$', home.index, name='index'),
                  re_path(r'^logout/$', home.logout, name='logout'),

                  # 项目列表
                  re_path(r'^project/list/$', project.project_list, name='project_list'),
                  re_path(r'^project/star/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_star,
                          name='project_star'),
                  re_path(r'^project/unstar/(?P<project_type>\w+)/(?P<project_id>\d+)/$', project.project_unstar,
                          name='project_unstar'),

                  # 项目管理
                  re_path(r'^manage/(?P<project_id>\d+)/', include([
                      re_path(r'^dashboard/$', manage.dashboard, name='dashboard'),

                      re_path(r'^statistics/$', manage.statistics, name='statistics'),

                      re_path(r'^wiki/$', wiki.wiki, name='wiki'),
                      re_path(r'^wiki/add/$', wiki.wiki_add, name='wiki_add'),
                      re_path(r'^wiki/catalog/$', wiki.wiki_catalog, name='wiki_catalog'),
                      re_path(r'^wiki/delete/(?P<wiki_id>\d+)/$', wiki.delete, name='wiki_delete'),
                      re_path(r'^wiki/edit/(?P<wiki_id>\d+)/$', wiki.edit, name='wiki_edit'),
                      re_path(r'^wiki/upload/$', wiki.wiki_upload, name='wiki_upload'),

                      re_path(r'^file/$', file.file, name='file'),
                      re_path(r'^file/delete/$', file.file_delete, name='filedelete'),
                      re_path(r'^file/post/$', file.file_post, name='file_post'),
                      re_path(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),
                      re_path(r'^cos/credential/$', file.cos_credential, name='cos_credential'),
                      # url(r'^file/download/(?P<file_id>\d+)/$', file.file_download, name='file_download'),

                      re_path(r'^setting/$', viewsetting.setting, name='setting'),

                      re_path(r'^setting/delete/$', viewsetting.setting_delete, name='settingdelete'),

                      re_path(r'^issues/$', issues.issues, name='issues'),

                  ])),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

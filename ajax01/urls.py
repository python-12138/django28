


from django.urls import path
from ajax01.views import *


urlpatterns = [
    path('ajax_hello/', ajax_hello),
    path('render_ajax/', render_ajax),
]

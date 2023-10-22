from django.urls import path
from .views import *


urlpatterns = [
    path('send/sms/<int:number>/',send_sms),
    path('register/', register),
    path('redis_index/', redis_index),
    path('redis_test/', return_test),
    path('datatest/', date_test),
    path('dictlist/', dictlist),
    path('formtest/', form_test),
]

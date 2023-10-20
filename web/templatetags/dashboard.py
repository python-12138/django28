from django.template import Library
from django.urls import reverse
from web import models

register = Library()



@register.simple_tag
def user_space(size):
    # 将传经来的值转换为 G 或者 M 的单位(传进来的单位是字节)
    if size < 1024:
        return "%.2f B" % size
    elif size < 1024 * 1024:
        return "%.2f KB" % (size / 1024)
    elif size < 1024 * 1024 * 1024:
        return "%.2f MB" % (size / (1024 * 1024))
    else:
        return "%.2f GB" % (size / (1024 * 1024 * 1024))

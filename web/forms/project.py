from django import forms
from django.core.validators import ValidationError
from web.forms.widgets import ColorRadioSelect
from web import models
from web.forms.bootstrap import BootStrapForm


class ProjectModelForm(BootStrapForm, forms.ModelForm):
    # desc = forms.CharField(widget=forms.Textarea)
    bootstrap_class_exclude = ['color']

    class Meta:
        model = models.Project
        fields = ['name', 'color', 'desc']
        widgets = {
            'desc': forms.Textarea,
            'color': ColorRadioSelect(attrs={'class': 'color-radio'}),
        }

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):

        name = self.cleaned_data['name']
        # 1.当前用户是否已经创建过此项目
        exists = models.Project.objects.filter(name=name, creator=self.request.tracer.user).exists()

        if exists:
            raise ValidationError('项目名称已经存在')

        # 2. 当前用户是否还有额度进行创建项目
        # 最多创建N个项目
        # self.request.tracer.price_policy.project_num
        # 现在已经创建的项目
        count = models.Project.objects.filter(creator=self.request.tracer.user).count()

        if count >= self.request.tracer.price_policy.project_num:
            raise ValidationError('项目个数超限，请购买套餐')

        return name

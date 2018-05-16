#coding=utf8

from django import forms
import string
from django.contrib.auth.admin import User
from django.forms import ModelForm, ModelChoiceField
from market.models import *


#注册
class Register(forms.Form):
    username = forms.CharField(max_length=20,label='用户名')
    passwd = forms.CharField(max_length=20,label='密码',widget=forms.PasswordInput)
    repasswd = forms.CharField(max_length=20,label='重复密码',widget=forms.PasswordInput)
    
    def clean_username(self):
        viavd = string.digits + string.ascii_letters
        name = self.cleaned_data['username']
        for i in name:
            if i not in viavd:
                raise forms.ValidationError('用户名不合法')
        p = User.objects.only('username').filter(username = name)
        if p:
            raise forms.ValidationError('用户名重复')
        return name

    def clean_repasswd(self):
        passwd = self.cleaned_data.get('passwd')
        repasswd = self.cleaned_data.get('repasswd')
        if passwd != repasswd:
            raise forms.ValidationError('两次密码不一致')
        return repasswd

#发布商品
class GoodsForm(ModelForm):
    #Gategory = ModelChoiceField(queryset=GoodsType.objects.all())  # 不分级单选可
    class Meta:
        model = GoodsMessage
        Gategory = ModelChoiceField(queryset=GoodsType.objects.all())  # 分级单选框
        fields = ['Title','Category','Details']
        labels = {
            'Title': '商品名',
            'Category': '分类',
        }
        widgets = {
            'Title': forms.TextInput(attrs={'class' : 'form-control',
                                            'id' : "inputCount3" ,
                                            'placeholder' : "",
            }),

            'Gategory' : forms.Select(attrs={'class' : "form-control",

            }),

            'Details' : forms.Textarea(attrs={'class' : "form-control",
                                              'rows' : 5 ,
                                              'id' : "introduction",

            })
        }
        
class UserMessage(ModelForm):
    class Meta:
        model=UserProfile
        fields = ['Nick']
        widgets = {
            'Nick': forms.TextInput(attrs={'class': 'form-control',
                                        'id': "inputCount3",
                                        'placeholder': "不要超过20个字",
                                        }),
        }

class GoodsWordsForm(forms.Form):
    Words = forms.CharField(label='',widget=forms.Textarea(attrs={'rows':3,'cols':50}))
    To = forms.IntegerField(widget=forms.HiddenInput,required=False)

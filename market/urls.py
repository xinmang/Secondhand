#coding=utf8
from django.conf.urls import url
from market.views import *

urlpatterns = (
url(r'^$', index),#首页
url(r'^register/$', register),#注册
url(r'^login/$', login),#登录
url(r'^logout/$', logout),#注销
url(r'^push_goods/$', push_goods),#发布物品
url(r'^goods/(?P<number>\d+)/$',look_goods),#查看物品
url(r'^goods/reply/$', goods_reply),#评论
url(r'^user/(?P<id>\d+)/$', look_user),#用户信息
url(r'^me/$', user_message),#个人信息
url(r'^edit/(?P<id>\d+)/$', edit_goods),#编辑物品
url(r'^add/pic/$', add_pic),#添加图片
url(r'^del/pic/$', del_pic),#删除图片
url(r'^del/good/(?P<id>\d+)/$', del_good),#删除物品
url(r'^del/word/$', del_good_words),#删除评论
url(r'^me/log/$', show_log),#未读消息
url(r'^log/read/$', read_log),#已读消息
url(r'^log/manager/$', log_manager),#管理消息
url(r'^me/edit/$', change_myself),#修改个人信息
)

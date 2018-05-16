#coding=utf8
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http import HttpResponse,Http404
from django.shortcuts import render
from django.conf import settings
from django.contrib import auth
from market.shuju import *
from market.forms import *
import os, random, datetime
from comm.comm_method import filetype,creat_head,create_code,creat_small_img


#注册
def register(request):
    if request.method == 'POST':
        form = Register(request.POST)
        if form.is_valid():  # 判断是否合法
            user = User.objects.create_user(username=form.cleaned_data['username']
                                            ,password=form.cleaned_data['passwd'])
            #user.date_joined = datetime.datetime.now()
            user.save()
            all_user = UserProfile()
            all_user.User = user
            all_user.Nick = user.username
            all_user.save()
            return HttpResponseRedirect('/')
    else:
        form = Register()
    return render(request, 'market/Register.html', {'form': form})

#登录
def login(request):
    if request.method == 'POST':
        name = request.POST.get('username','')
        passwd = request.POST.get('password','')
        user = auth.authenticate(username=name,password=passwd)
        if user is not None and user.is_active:
            auth.login(request,user)
            profile = UserProfile.objects.get(User=user)
            request.session['nick'] = profile.Nick
            request.session['avatar'] = profile.Avatar
            return HttpResponseRedirect('/')

        else:
            return render(request,'market/login.html',{'error':'用户名和密码不匹配！'})

    else:
        return render(request,'market/login.html')

#注销
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

#大图和小图
def save2images(file,goodsmessage):
    #如果media中不存在images目录，则创建
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'images')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'images'))
    #图片的全路径
    full_path = os.path.join(settings.MEDIA_ROOT, 'images' , file.name)
    file_name = file.name
    if(os.path.exists(full_path)):
        #新文件名添加了16位随机字符
        file_name = file_name[:-len(file_name.split('.')[-1]) - 1] + '_' + \
                   ''.join(random.sample(string.ascii_letters + string.digits, 16)) + \
                   '.' + file_name.split('.')[-1]
        full_path = os.path.join(settings.MEDIA_ROOT, 'images' , file_name)
    fd = open(full_path,'wb+')
    for chunks in file.chunks():
        fd.write(chunks)
    fd.close()
    #if(filetype(full_path) == 'unknown'):
        #os.remove(full_path)
        #return None
    #进行图片剪裁
    sm_img = creat_small_img(full_path)
    big_img = creat_small_img(full_path,'big')
    if big_img:
        os.remove(full_path)
    else:
        big_img = os.path.join('/media/images',os.path.basename(full_path))
    g = GoodsImage(ImgBig=big_img,ImgSma=sm_img)
    g.save()
    goodsmessage.Images.add(g)
    #如果无图就添加一张新图
    if not goodsmessage.First_pic:
        goodsmessage.First_pic = g
        goodsmessage.save()


#发布商品
@login_required
def push_goods(request):
    f = GoodsForm()
    code_err = False
    if request.method == 'POST':
        f = GoodsForm(request.POST,request.FILES)
        if f.is_valid():
            e_f = f.save(commit=False)
            e_f.Ctime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            e_f.Mtime = e_f.Ctime
            e_f.Owner = request.user
            e_f.save()

            # 获取上传文件列表
            f = request.FILES.getlist('image')

            if(f):
                good = GoodsMessage.objects.get(id = e_f.id)
                for p in f:
                    save2images(p,good)

            return HttpResponseRedirect('/goods/'+str(e_f.id))

    return render(request, 'market/PushGoods.html',{'form':f,'code_err':code_err})


#查看商品具体信息
def look_goods(request,number):
    goods = GoodsMessage.objects.filter(id = number).first()
    if(goods):
        profile = UserProfile.objects.get(User=goods.Owner)
        #增加访问量
        goods.PV = goods.PV + 1
        goods.save()
        #抓取图片
        image = goods.Images.all()
        #抓取回复
        words = GoodsWords.objects.filter(Owner=goods,Display=True)
        user = request.user
        f = GoodsWordsForm()
        return render(request,'market/GoodsMessage.html',{'uid':user.id,'words':words,'form':f,'profile':profile,'goods':goods,'image':image})
    else:
        raise Http404()




#首页显示所有商品
def index(request):
    goods = GoodsMessage.objects.filter(Is_alive=True)
    return render(request,'market/index.html',{'goods':goods})


#添加留言推送
def add_push_mess(good,reply,user):
    log = GoodsLog()
    log.Owner = good
    log.From = UserProfile.objects.filter(User=user).first()
    if not reply.To:
        log.To = good.Owner
    else:
        log.To = reply.To.From.User
    log.Mess = reply
    log.save()

#发布商品留言
@login_required
def goods_reply(request):

    #只接受POST
    if request.method != "POST":
        raise Http404()


    f = GoodsWordsForm(request.POST)
    if(f.is_valid()):
        owner = request.POST.get('goods_id',None)
        goods = GoodsMessage.objects.filter(id=owner,Is_alive=True).first()
        # 发表留言所属的商品不存在或已经下架
        if not owner or not goods:
            return HttpResponse("似乎有点问题，重试试吧！")

        reply = GoodsWords()
        reply.Words = f.cleaned_data['Words']
        reply.Time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        reply.Owner = goods
        reply.From = UserProfile.objects.get(User=request.user)
        to = f.cleaned_data['To']
        #验证回复给的留言是否属于该商品
        t = GoodsWords.objects.filter(id=to,Owner=goods).first()
        if to and t:
            reply.To = t
        reply.save()
        #添加留言推送
        add_push_mess(goods,reply,request.user)
        return HttpResponseRedirect('/goods/'+str(goods.id))
    else:
        return HttpResponse('请正确填写回复内容')


#查看别人信息
def look_user(request,id):
    profile = UserProfile.objects.filter(User=id).first()
    if(not profile):
        raise Http404()
    #不能用values查询,values返回的是字典而不是QuerySet
    goods = GoodsMessage.objects.filter(Is_alive=True,Owner=id)
    return render(request,'market/UserMessage.html', {'profile':profile,'goods': goods})

#个人信息
@login_required
def user_message(request):
    user = request.user
    profile = UserProfile.objects.get(User=user)
    #包含下架商品
    goods = GoodsMessage.objects.filter(Owner=user)

    #系统通知个数
    log = len(GoodsLog.objects.filter(To = user,Readed=False))

    return render(request,'market/MyMessage.html', {'log':log,'profile': profile, 'goods': goods})

#编辑商品
@login_required
def edit_goods(request,id):
    type = GoodsType.objects.all()
    user = request.user
    goods = GoodsMessage.objects.filter(id=id,Is_alive=True,Owner=user).first()
    if not goods:
        raise Http404()
    if request.method == 'POST':
        form = GoodsForm(request.POST,instance=goods)
        if form.is_valid():
            e_f = form.save(commit=False)
            e_f.Mtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            e_f.save()
            return HttpResponseRedirect('/edit/'+str(e_f.id))
    else:
        form = GoodsForm(instance=goods)
    pic = goods.Images.all()
    return render(request,'market/Edit.html',{'type':type,'form':form,'image':pic,'id':goods.id})

#商品添加图片
@login_required
def add_pic(request):
    if request.method != 'POST':
        raise Http404()
    id = request.POST.get('goods_id',None)
    goods = GoodsMessage.objects.filter(id = id,Is_alive=True).first()
    if not goods:
        raise Http404()
    f = request.FILES.getlist('image')
    if (f):
        for i in f:
            save2images(i, goods)
    return HttpResponseRedirect("/edit/"+id)

# 删除img的大小两个文件
def img_file_del(image):
    pic = str(image.ImgBig)
    mini = str(image.ImgSma)
    try:
        os.remove(settings.MEDIA_ROOT+'/../'+pic)
        os.remove(settings.MEDIA_ROOT+'/../'+mini)
    except:
        os.remove(settings.MEDIA_ROOT+'/../'+mini)

#删除商品图片
@login_required
def del_pic(request):
    goods_id = request.GET.get('goods_id',None)
    image_id = request.GET.get('image_id',None)
    if(not goods_id or not image_id):
        raise Http404()
    goods = GoodsMessage.objects.filter(id=goods_id,Is_alive=True).first()
    image = goods.Images.filter(id=image_id).first()
    if not image:
        raise Http404()

    #先将第一张图置空，然后重新保存
    goods.First_pic = None
    goods.save()

    #删除商品图片关联
    goods.Images.remove(image)

    #删除磁盘文件
    img_file_del(image)

    #删除商品图片表记录
    image.delete()

    #添加首图
    goods.First_pic = goods.Images.first()
    goods.save()
    return HttpResponseRedirect('/edit/'+goods_id)

#删除商品
@login_required
def del_good(request,id):
    user = request.user
    good = GoodsMessage.objects.filter(id = id).first()
    if not good:
        raise Http404()

    #删除评论

    words = GoodsWords.objects.filter(Owner = good).delete()

    #删除图片
    image = good.Images.all()
    for i in image:
        img_file_del(i)

    image.delete()

    #删除相关提醒
    GoodsLog.objects.filter(Owner=good).delete()

    #删除商品
    good.delete()

    return HttpResponseRedirect("/me/")

#删除评论
@login_required
def del_good_words(request):
    good_id = request.GET.get('good_id',None)
    word_id = request.GET.get('word_id',None)
    good = GoodsMessage.objects.filter(id = good_id).first()
    word = GoodsWords.objects.filter(Owner=good,id=word_id).first()
    if not word:
        raise Http404()
    user = request.user
    if word.From.User == user:
        word.Display = False
        word.save()
        return HttpResponseRedirect('/goods/'+good_id)
    raise Http404()

#显示提示
@login_required
def show_log(request):
    user = request.user
    Newlog = GoodsLog.objects.filter(To=user,Readed=False)
    Oldlog = GoodsLog.objects.filter(To=user,Readed=True)

    return render(request,"market/MyLog.html",{'Newlog':Newlog,'Oldlog':Oldlog})

#读消息中转页面
@login_required
def read_log(request):
    id = request.GET.get('id',None)
    log = GoodsLog.objects.filter(To=request.user,id=id).first()
    if not log:
        raise Http404()

    if log.Readed == False:
        log.Readed = True
        log.save()

    return HttpResponseRedirect('/goods/'+str(log.Owner.id))

#消息处理页面 /log/mamager/?method=*&id=*
@login_required
def log_manager(request):
    def Del_all():
        GoodsLog.objects.filter(To=request.user).delete()

    def Del_old():
        GoodsLog.objects.filter(To=request.user,Readed=True).delete()

    def Read_new():
        logs = GoodsLog.objects.filter(To=request.user,Readed=False)
        for i in logs:
            i.Readed = True
            i.save()

    def Del_each():
        GoodsLog.objects.filter(To=request.user, id=id).delete()


    method = request.GET.get('method', None)
    id = request.GET.get('id', None)

    switcher = {
        'del_all' : Del_all,  # 删除所有消息
        'del_old' : Del_old,  # 删除所有旧消息
        'read_new' : Read_new, # 标记所有为已读
        'del_each' : Del_each  # 删除单条
    }

    end = switcher.get(method,None)
    if end:
        end()
        return HttpResponseRedirect('/me/log/')
    raise Http404()


#保存头像
def savehead(pic):
    #如果media不存在head文件夹，就创建
    if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'head')):
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'head'))
    randname = ''.join(random.sample(string.ascii_letters + string.digits, 24))
    randname += '.' + pic.name.split('.')[-1]
    full_path = os.path.join(settings.MEDIA_ROOT, 'head', randname)
    fd = open(full_path, 'wb+')
    for chunks in pic.chunks():
        fd.write(chunks)
    fd.close()
    if (filetype(full_path) == 'unknown'):
        os.remove(full_path)
        return None
    else:
        nn = creat_head(full_path)
        os.remove(full_path)
        return nn



#修改自身信息
@login_required
def change_myself(request):
    profile = UserProfile.objects.get(User=request.user)
    if request.method != 'POST':
        form = UserMessage(instance=profile)
    else:
        form = UserMessage(request.POST)
        if form.is_valid():
            profile.Nick = form.cleaned_data['Nick']
            profile.save()
            request.session['nick'] = profile.Nick

            pic = request.FILES.get('Avatar')
            if pic:
                nn = savehead(pic)
                if nn:
                    #非系统图片就删除以前的图片
                    if(str(profile.Avatar)[:6] == '/media'):
                        os.remove(settings.BASE_DIR+str(profile.Avatar))

                    profile.Avatar = nn
                    profile.save()
                    request.session['avatar'] = nn
                    
    return render(request,'market/ChangeMyself.html',
                  {'profile':profile,'form':form,'user': request.user})

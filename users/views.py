from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.http import HttpResponse
from django_redis import get_redis_connection
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

from libs.captcha.captcha import captcha
from utils.response_code import RETCODE
from libs.yuntongxun.sms import CCP
from users.models import User
from home.models import ArticleCategory, Article

import re
from random import randint
import logging

logger = logging.getLogger('django')


# 注册视图
class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # 1.接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证数据
        if not all([mobile, password, password2, smscode]):  # 验证数据是否齐全
            return HttpResponseBadRequest('缺少必要参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('输入8-20位密码，密码是数字下划线')
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('验证码已经过期')
        if smscode != redis_sms_code.decode():
            # return HttpResponseBadRequest('短信验证码不一致')
            pass
        # 3.将注册信息保存数据库
        try:  # create_user可以使用系统的方法对密码加密
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')
        login(request, user)  # 状态保持
        # 4.返回响应到指定页面，redirect适用于重定向的，reverse可以通过namespace:name来获取到视图所对应的路由
        response = redirect(reverse('home:index'))
        # 设置cookie信息，以方便在首页中用户信息展示的判断和用户信息的展示
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age=7 * 24 * 3600)
        return response


class ImageCodeView(View):
    def get(self, request):
        uuid = request.GET.get('uuid')  # 1.接收前端传过来的uuid
        if uuid is None:  # 2.判断uuid是否获取到
            return HttpResponseBadRequest('没有传递uuid')
        text, image = captcha.generate_captcha()  # 3.通过调用captcha来生成图片验证码
        # 4.将图片内容保存在redis中，uuid作为一个key，同时设置一个实效300秒
        redis_conn = get_redis_connection('default')
        redis_conn.setex('img:%s' % uuid, 300, text)
        # 5.将图片二进制返回给前端
        return HttpResponse(image, content_type='image/jpeg')


class SmsCodeView(View):
    def get(self, request):
        # 1.接收参数，以查询字符串的形式传递
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 2.参数验证
        if not all([mobile, image_code, uuid]):  # 验证参数是否齐全
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必要的参数'})
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)
        if redis_image_code is None:  # 验证图片验证码
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码已经过期'})
        try:  # 如果未过期，获取到之后就可以删除图片验证码
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 比对图片验证码，注意大小写，redis的数据是bytes类型
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码错误'})
        # 3.生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)
        # 4.短信验证码保存到redis中
        redis_conn.setex('sms:%s' % mobile, 300, sms_code)
        # 5.开始发送短信
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        # 6.返回响应
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '短信发送成功'})


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # 1.接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 2.参数验证
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')
        # 3.用户认证登录，采用系统自带的认证方式，正确返回user，错误返回None
        # 默认方式是针对username字段进行用户名的判断，当前判断信息是手机号，需要修改认证字段
        user = authenticate(mobile=mobile, password=password)
        if user is None:
            return HttpResponseBadRequest('手机号或者面错误')
        # 4.状态的保持
        login(request, user)
        # 5.根据选择是否记住登陆状态来判断
        # 6.为了首页显示我们要设置一些cookie信息
        # 根据next参数进行页面跳转
        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:
            response = redirect(reverse('home:index'))
        if remember != 'on':  # 没有记住用户信息
            request.session.set_expiry(0)  # 浏览器关闭之后失效
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        else:  # 记住用户信息
            request.session.set_expiry(None)  # 默认是两周
            response.set_cookie('is_login', True, max_age=14 * 24 * 3600)
            response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        # 7.返回响应
        return response


class LogoutView(View):
    def get(self, request):
        # 1.session数据清除
        logout(request)
        # 2.cookie数据的部分删除
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # 3.跳转到首页
        return response


class ForgetPasswordView(View):
    def get(self, request):
        return render(request, 'forget_password.html')

    def post(self, request):
        # 1.接收数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')
        # 2.验证数据
        if not all([mobile, password, password2, smscode]):  # 验证数据是否齐全
            return HttpResponseBadRequest('缺少必要参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseBadRequest('输入8-20位密码，密码是数字下划线')
        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s' % mobile)
        if redis_sms_code is None:
            return HttpResponseBadRequest('验证码已经过期')
        if smscode != redis_sms_code.decode():
            # return HttpResponseBadRequest('短信验证码不一致')
            pass
        # 3.根据手机号进行用户信息的查询
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:  # 5.没有查询出信息就进行新用户的创建
            try:
                User.objects.create_user(username=mobile, mobile=mobile, password=password)
            except Exception as e:
                logger.error(e)
                return HttpResponseBadRequest('创建失败，请稍后再试')
        else:  # 4.没问题则进行修改
            user.set_password(password)
            user.save()  # 一定要注意保存信息
        # 6.进行页面跳转，跳转到登录页面
        response = redirect(reverse('user:login'))
        # 7.返回响应
        return response


class UserCenterView(LoginRequiredMixin, View):
    # LoginRequiredMixin 如果用户未登录，就会进行默认跳转，链接是：account/login/?next=xxx
    def get(self, request):
        user = request.user  # 获取用户信息
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc': user.user_desc
        }
        return render(request, 'center.html', context=context)

    def post(self, request):
        user = request.user
        username = request.POST.get('username', user.username)
        user_desc = request.POST.get('desc', user.user_desc)
        avatar = request.FILES.get('avatar')
        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败，请稍后再试')
        response = redirect(reverse('users:center'))
        response.set_cookie('username', user.username, max_age=14 * 24 * 3600)
        return response


class WriteBlogView(LoginRequiredMixin, View):
    def get(self, request):
        # 查询所有的分类
        categories = ArticleCategory.objects.all()
        context = {'categories': categories}
        return render(request, 'write_blog.html', context=context)

    def post(self, request):
        # 1.接收数据
        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        summary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user
        # 2.验证数据
        if not all(['avatar, title, category_id, summary, content']):
            return HttpResponseBadRequest('参数不全')
        try:
            category = ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类')
        # 3.数据入库
        try:
            article = Article.objects.create(
                author=user,
                avatar=avatar,
                title=title,
                category=category,
                tags=tags,
                summary=summary,
                content=content
            )
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('发布失败，请稍后再试')
        # 4。跳转到指定页面
        response = redirect(reverse('home:index'))
        return response



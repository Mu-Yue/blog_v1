from django.urls import path

from users.views import RegisterView, ImageCodeView, SmsCodeView, LoginView, LogoutView, ForgetPasswordView
from users.views import UserCenterView, WriteBlogView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # 注册路由
    path('imagecode/', ImageCodeView.as_view(), name='imagecode'),  # 图片验证码
    path('smscode/', SmsCodeView.as_view(), name='smscode'),  # 图片验证码
    path('login/', LoginView.as_view(), name='login'),  # 登录路由
    path('logout/', LogoutView.as_view(), name='logout'),  # 退出登录
    path('forgetpassword/', ForgetPasswordView.as_view(), name='forgetpassword'),  # 忘记密码
    path('center/', UserCenterView.as_view(), name='center'),  # 用户中心
    path('writeblog/', WriteBlogView.as_view(), name='writeblog'),  # 写博客
]


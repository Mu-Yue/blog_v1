"""blog_v1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # include()中有两个参数，需要设置一个元组 urlconf_module, app_name
    # urlconf_module: 子应用的路由
    # app_name: 子应用的名字
    # namespace: 命名空间
    path('', include(('users.urls', 'users'), namespace='users')),
    path('', include(('home.urls', 'home'), namespace='home')),
]

# 图片路由的访问
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

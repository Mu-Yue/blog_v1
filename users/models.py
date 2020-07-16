from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    mobile = models.CharField(max_length=11, unique=True, blank=False)  # 设置手机号
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)  # 设置头像信息
    user_desc = models.CharField(max_length=500, blank=True)  # 个人简介

    USERNAME_FIELD = 'mobile'  # 修改认证字段为手机号

    # 创建超级管理员必须输入字段（不包括手机号和密码）
    REQUIRED_FIELDS = ['username', 'email']

    class Meta:
        db_table = 'tb_users'  # 修改表名
        verbose_name = '用户管理'  # admin后台显示
        verbose_name_plural = verbose_name  # admin后台显示（复数形式）

    def __str__(self):
        return self.mobile



from django.db import models
from django.utils import timezone

from users.models import User


class ArticleCategory(models.Model):
    title = models.CharField(max_length=100, blank=True)  # 分类标题
    created = models.DateTimeField(default=timezone.now)  # 分类创建时间

    # admin站点显示，方便查看
    def __str__(self):
        return self.title

    class Meta:
        db_table = 'tb_category'  # 修改表名
        verbose_name = '类别管理'  # admin站点显示
        verbose_name_plural = verbose_name


class Article(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='article/%Y%m%d', blank=True)
    title = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(ArticleCategory, null=True, blank=True, on_delete=models.CASCADE, related_name='article')
    tags = models.CharField(max_length=20, blank=True)
    summary = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField()
    total_views = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tb_article'
        ordering = ('-created',)
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Comment(models.Model):
    content = models.TextField()
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.article.title

    class Meta:
        db_table = 'tb_comment'
        verbose_name = '评论管理'
        verbose_name_plural = verbose_name

from django.shortcuts import render, redirect, reverse
from django.views import View
from django.http.response import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage

from home.models import Article, ArticleCategory, Comment


class IndexView(View):
    def get(self, request):
        # 1.获取所有分类信息
        categories = ArticleCategory.objects.all()
        # 2.接收用户点击的分类id
        cat_id = request.GET.get('cat_id', 1)
        # 3.根据分类ID进行分类查询
        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')
        # 4.获取分页参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)
        # 5.根据分类信息查询文章
        articles = Article.objects.filter(category=category)
        # 6.创建分页
        paginator = Paginator(articles, per_page=page_size)
        # 7.进行分页处理
        try:
            page_articles = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('Empty Page')
        total_page = paginator.num_pages  # 总页数
        # 8.组织数据传递给模板
        context = {
            'categories': categories,
            'category': category,
            'articles': page_articles,
            'page_size': page_size,
            'total_page': total_page,
            'page_num': page_num
        }
        return render(request, 'index.html', context=context)


class DetailView(View):
    def get(self, request):
        # 1.接收文章ID信息
        id = request.GET.get('id')
        # 2.根据id进行查询
        try:
            article = Article.objects.get(id=id)
        except Article.DoesNotExist:
            return render(request, '404.html')
        else:
            article.total_views += 1  # 让文章浏览量加1
            article.save()
        # 3.查询分类数据
        categories = ArticleCategory.objects.all()
        hot_articles = Article.objects.order_by('-total_views')[0:9]

        page_size = request.GET.get('page_size', 10)
        page_num = request.GET.get('page_num', 1)
        comments = Comment.objects.filter(article=article).order_by('-created')
        total_count = comments.count()
        paginator = Paginator(comments, page_size)
        try:
            page_comments = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('Empty Page')
        total_page = paginator.num_pages
        # 4.组织模板信息
        context = {
            'categories': categories,
            'category': article.category,
            'article': article,
            'hot_articles': hot_articles,
            'comments': page_comments,
            'total_count': total_count,
            'total_page': total_page,
            'page_size': page_size,
            'page_num': page_num
        }
        return render(request, 'detail.html', context=context)

    def post(self, request):
        # 1.接收用户信息
        user = request.user
        # 2.判断用户是否登陆
        if user and user.is_authenticated:  # 3.登录用户接收form数据
            id = request.POST.get('id')
            content = request.POST.get('content')
            try:
                article = Article.objects.get(id=id)
            except Article.DoesNotExist:
                return HttpResponseNotFound('没有此文章')
            Comment.objects.create(content=content, article=article, user=user)
            article.comments_count += 1
            article.save()
            path = reverse('home:detail') + '?id={}'.format(article.id)
            return redirect(path)
        else:  # 4.未登录用户跳转到登录页面
            return request(reverse('users:login'))





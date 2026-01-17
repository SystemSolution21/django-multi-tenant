# blog/views.py

# Import django libraries
from django.db.models.manager import BaseManager
from rest_framework import viewsets

# Import local modules
from blog.models import Article
from blog.serializers import ArticleSerializer


class ArticleViewSet(viewsets.ModelViewSet):
    """
    A viewset for the Article model.
    """

    queryset: BaseManager[Article] = Article.objects.all()
    serializer_class = ArticleSerializer

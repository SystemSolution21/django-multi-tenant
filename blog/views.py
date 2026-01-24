# blog/views.py

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework import viewsets

# Import local modules
from blog.models import Article
from blog.serializers import ArticleSerializer


# ============================================================================
# REST API Views
# ============================================================================


class ArticleViewSet(viewsets.ModelViewSet):
    """
    A viewset for the Article model.
    """

    queryset: BaseManager[Article] = Article.objects.all()
    serializer_class = ArticleSerializer


# ============================================================================
# Web UI Views (Public Schema Only)
# ============================================================================


class ArticleListView(ListView):
    """
    List all blog articles (public schema).
    """

    model = Article
    template_name = "blog/article_list.html"
    context_object_name = "articles"
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Article]:
        """Get all articles ordered by creation date."""
        return Article.objects.all().order_by("-created_at")


class ArticleDetailView(DetailView):
    """
    Display a single blog article.
    """

    model = Article
    template_name = "blog/article_detail.html"
    context_object_name = "article"


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_form.html"
    fields = ["title", "content"]
    success_url = reverse_lazy("article_list")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article creation."""
        messages.success(self.request, "Article created successfully!")
        return super().form_valid(form)


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_form.html"
    fields = ["title", "content"]
    success_url = reverse_lazy("article_list")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article update."""
        messages.success(self.request, "Article updated successfully!")
        return super().form_valid(form)


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_confirm_delete.html"
    success_url = reverse_lazy("article_list")

    def delete(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Add success message on article deletion."""
        messages.success(request, "Article deleted successfully!")
        return super().delete(request, *args, **kwargs)

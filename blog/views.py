# blog/views.py

# Import standard libraries
from typing import cast

# Import django libraries
from django import forms
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

# Import third-party libraries
import structlog

# Import local modules
from blog.models import Article, Category, Tag
from blog.serializers import ArticleSerializer

# Initialize logger
logger = structlog.get_logger(__name__)

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
# Web UI Views
# ============================================================================


class ArticleListView(ListView):
    """
    List all blog articles.
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

    def get_object(self, queryset=None):
        self.obj = super().get_object(queryset)
        self.obj = cast(Article, self.obj)
        # Increment view count
        self.obj.views_count += 1
        self.obj.save(update_fields=["views_count"])
        return self.obj


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_form.html"
    fields = [
        "title",
        "slug",
        "excerpt",
        "content",
        "featured_image",
        "status",
        "publish_date",
        "category",
        "tags",
    ]
    success_url = reverse_lazy("article_list")

    def get_form(self, form_class=None):
        """Customize the form widget for publish_date."""
        form = super().get_form(form_class)
        # Use HTML5 datetime-local input for a browser-native calendar picker
        form.fields["publish_date"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local"}
        )
        return form

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article creation and log the event."""

        # Assign current user as author
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(request=self.request, message="Article created successfully!")
        logger.info(
            "article_created",
            title=form.instance.title,
            article_id=form.instance.pk,
            user_id=self.request.user.pk,
        )
        return response


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_form.html"
    fields = [
        "title",
        "slug",
        "excerpt",
        "content",
        "featured_image",
        "status",
        "publish_date",
        "category",
        "tags",
    ]
    success_url = reverse_lazy("article_list")

    def get_form(self, form_class=None):
        """Customize the form widget for publish_date."""
        form = super().get_form(form_class)
        # Use HTML5 datetime-local input for a browser-native calendar picker
        form.fields["publish_date"].widget = forms.DateTimeInput(
            attrs={"type": "datetime-local"}
        )
        return form

    def get_queryset(self) -> QuerySet[Article]:
        """Only allow authors to edit their own articles."""
        return super().get_queryset().filter(author=self.request.user)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article update and log the event."""

        messages.success(self.request, "Article updated successfully!")
        response = super().form_valid(form)
        logger.info(
            "article_updated",
            title=form.instance.title,
            article_id=form.instance.pk,
            user_id=self.request.user.pk,
        )
        return response


class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a blog article (requires authentication).
    """

    model = Article
    template_name = "blog/article_confirm_delete.html"
    success_url = reverse_lazy("article_list")

    def get_queryset(self) -> QuerySet[Article]:
        """Only allow authors to delete their own articles."""
        return super().get_queryset().filter(author=self.request.user)

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Override post to log the deletion event before the object is deleted.
        """
        self.object = self.get_object()
        article = cast(Article, self.object)

        logger.info(
            "article_deleted",
            title=article.title,
            article_id=article.pk,
            user_id=request.user.pk,
        )
        messages.success(request, "Article deleted successfully!")

        # The parent's post() method calls the original delete().
        return super().post(request, *args, **kwargs)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new category.
    """

    model = Category
    fields = ["name", "description"]
    template_name = "blog/article_form.html"  # Reusing the generic form template
    success_url = reverse_lazy("article_create")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, f"Category '{form.instance.name}' created!")
        return super().form_valid(form)


class TagCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new tag.
    """

    model = Tag
    fields = ["name"]
    template_name = "blog/article_form.html"  # Reusing the generic form template
    success_url = reverse_lazy("article_create")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        messages.success(self.request, f"Tag '{form.instance.name}' created!")
        return super().form_valid(form)

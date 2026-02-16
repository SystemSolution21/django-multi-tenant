# blog/views.py

# Import standard libraries
from typing import cast

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
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
from blog.forms import ArticleForm, CategoryForm, TagForm
from blog.serializers import ArticleSerializer
from tenants.models import User

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
    form_class = ArticleForm
    template_name = "blog/article_form.html"
    success_url = reverse_lazy("article_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Restore form data from session if available (e.g. returning from category creation)
        if "article_form_data" in self.request.session:
            kwargs["data"] = self.request.session.pop("article_form_data")
        kwargs["request"] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        # Handle custom action buttons (Create Category/Tag)
        if "action" in request.POST:
            action = request.POST["action"]
            if action in ["create_category", "create_tag"]:
                # Serialize POST data to preserve user input
                form_data = {}
                for key, values in request.POST.lists():
                    if key == "csrfmiddlewaretoken":
                        continue
                    # Keep lists for M2M fields (tags) or if multiple values exist
                    if key == "tags" or len(values) > 1:
                        form_data[key] = values
                    else:
                        form_data[key] = values[0]

                request.session["article_form_data"] = form_data

                if action == "create_category":
                    return redirect(f"{reverse('category_create')}?next={request.path}")
                elif action == "create_tag":
                    return redirect(f"{reverse('tag_create')}?next={request.path}")

        return super().post(request, *args, **kwargs)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article creation and log the event."""

        # Assign current user as author
        form.instance.author = self.request.user
        response = super().form_valid(form)
        user = cast(User, self.request.user)
        messages.success(request=self.request, message="Article created successfully!")
        logger.info(
            "article_created",
            title=form.instance.title,
            article_id=form.instance.pk,
            created_by=user.full_name,
            user_id=self.request.user.pk,
        )
        return response


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing blog article (requires authentication).
    """

    model = Article
    form_class = ArticleForm
    template_name = "blog/article_form.html"
    success_url = reverse_lazy("article_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Restore form data from session if available
        if "article_form_data" in self.request.session:
            kwargs["data"] = self.request.session.pop("article_form_data")
        kwargs["request"] = self.request
        return kwargs

    def post(self, request, *args, **kwargs):
        # Handle custom action buttons (Create Category/Tag)
        if "action" in request.POST:
            action = request.POST["action"]
            if action in ["create_category", "create_tag"]:
                # Serialize POST data to preserve user input
                form_data = {}
                for key, values in request.POST.lists():
                    if key == "csrfmiddlewaretoken":
                        continue
                    if key == "tags" or len(values) > 1:
                        form_data[key] = values
                    else:
                        form_data[key] = values[0]

                request.session["article_form_data"] = form_data

                if action == "create_category":
                    return redirect(f"{reverse('category_create')}?next={request.path}")
                elif action == "create_tag":
                    return redirect(f"{reverse('tag_create')}?next={request.path}")

        return super().post(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Article]:
        """Only allow authors to edit their own articles."""
        return super().get_queryset().filter(author=self.request.user)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        """Add success message on article update and log the event."""

        response = super().form_valid(form)
        user = cast(User, self.request.user)
        messages.success(self.request, "Article updated successfully!")
        logger.info(
            "article_updated",
            title=form.instance.title,
            article_id=form.instance.pk,
            updated_by=user.full_name,
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
        user = cast(User, self.request.user)
        logger.info(
            "article_deleted",
            title=article.title,
            article_id=article.pk,
            deleted_by=user.full_name,
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
    form_class = CategoryForm
    template_name = "blog/article_form.html"  # Reusing the generic form template
    extra_context = {
        "title": "Create Category",
        "btn_text": "Save Category",
    }

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("article_create")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        user = cast(User, self.request.user)
        response = super().form_valid(form)
        messages.success(self.request, f"Category '{form.instance.name}' created!")
        logger.info(
            "category_created",
            category_name=form.instance.name,
            category_id=form.instance.pk,
            created_by=user.full_name,
            user_id=self.request.user.pk,
        )
        return response


class TagCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new tag.
    """

    model = Tag
    form_class = TagForm
    template_name = "blog/article_form.html"  # Reusing the generic form template
    extra_context = {
        "title": "Create Tag",
        "btn_text": "Save Tag",
    }

    def get_success_url(self):
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("article_create")

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        response = super().form_valid(form)
        user = cast(User, self.request.user)
        messages.success(self.request, f"Tag '{form.instance.name}' created!")
        logger.info(
            "tag_created",
            tag_name=form.instance.name,
            tag_id=form.instance.pk,
            created_by=user.full_name,
            user_id=self.request.user.pk,
        )
        return response

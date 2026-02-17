# tasks/views.py

# Import standard libraries
from typing import TYPE_CHECKING, cast

# Import django libraries
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Q, QuerySet
from django.forms import ModelChoiceField
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework.viewsets import ModelViewSet

# Import third-party libraries
import structlog

# Import local modules
from tasks.models import Project, Task
from tasks.serializers import ProjectSerializer, TaskSerializer
from tenants.mixins import TenantSchemaRequiredMixin
from tenants.models import User

# Initialize logger
logger = structlog.get_logger(__name__)

# ============================================================================
# API ViewSets (REST Framework)
# ============================================================================


class ProjectViewSet(ModelViewSet):
    """
    A viewset for the Project model (API).
    """

    queryset: QuerySet[Project] = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(ModelViewSet):
    """
    A viewset for the Task model (API).
    """

    queryset: QuerySet[Task] = Task.objects.select_related("project").all()
    serializer_class = TaskSerializer


# ============================================================================
# Web Views (Template-based)
# ============================================================================


class ProjectListView(LoginRequiredMixin, TenantSchemaRequiredMixin, ListView):
    """List all projects in the current tenant."""

    model = Project
    template_name = "tasks/project_list.html"
    context_object_name = "projects"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Project]:
        return Project.objects.select_related("owner").all()


class ProjectDetailView(LoginRequiredMixin, TenantSchemaRequiredMixin, DetailView):
    """Show project details and its tasks."""

    if TYPE_CHECKING:
        object: Project

    model = Project
    template_name = "tasks/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get tasks for this project
        context["tasks"] = Task.objects.filter(project=self.object).select_related(
            "assignee"
        )
        return context


class ProjectCreateView(LoginRequiredMixin, TenantSchemaRequiredMixin, CreateView):
    """Create a new project."""

    model = Project
    template_name = "tasks/project_form.html"
    fields = ["key", "name", "description", "owner"]
    success_url = reverse_lazy("project_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        if connection.schema_name != "public":
            owner_field = cast(ModelChoiceField, form.fields["owner"])
            owner_field.queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form

    def form_valid(self, form) -> HttpResponse:
        # Set the owner to current user if not specified
        if not form.instance.owner:
            form.instance.owner = self.request.user

        # Save the project
        response: HttpResponse = super().form_valid(form=form)

        messages.success(request=self.request, message="Project created successfully!")
        logger.info(
            "Project created",
            project=form.instance.name,
            project_id=form.instance.pk,
            owner_name=cast(User, form.instance.owner).full_name,
            owner_id=self.request.user.pk,
        )
        return response


class ProjectUpdateView(LoginRequiredMixin, TenantSchemaRequiredMixin, UpdateView):
    """Update an existing project."""

    model = Project
    template_name = "tasks/project_form.html"
    fields = ["key", "name", "description", "owner"]
    success_url = reverse_lazy("project_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        if connection.schema_name != "public":
            owner_field = cast(ModelChoiceField, form.fields["owner"])
            owner_field.queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form

    def form_valid(self, form) -> HttpResponse:
        response: HttpResponse = super().form_valid(form=form)
        messages.success(request=self.request, message="Project updated successfully!")
        logger.info(
            "Project updated",
            project=form.instance.name,
            project_id=form.instance.pk,
            owner_name=cast(User, form.instance.owner).full_name,
            owner_id=self.request.user.pk,
        )
        return response


class ProjectDeleteView(LoginRequiredMixin, TenantSchemaRequiredMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "tasks/project_confirm_delete.html"
    success_url = reverse_lazy("project_list")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Override post to log the deletion event before the object is deleted.
        """
        self.object = self.get_object()
        project = cast(Project, self.object)
        messages.success(request=self.request, message="Project deleted successfully!")
        logger.info(
            "Project deleted",
            project=project.name,
            project_id=project.pk,
            owner_name=cast(User, self.request.user).full_name,
            owner_id=self.request.user.pk,
        )
        # The parent's post() method calls the original delete().
        return super().post(request, *args, **kwargs)


class TaskListView(LoginRequiredMixin, TenantSchemaRequiredMixin, ListView):
    """List all tasks in the current tenant."""

    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Task]:
        queryset = Task.objects.select_related("project", "assignee").all()

        # Filter by status
        status = self.request.GET.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by priority
        priority = self.request.GET.get("priority")
        if priority:
            queryset = queryset.filter(priority=priority)

        # Filter by assignee
        assignee = self.request.GET.get("assignee")
        if assignee:
            if assignee == "me":
                queryset = queryset.filter(assignee=self.request.user)
            elif assignee == "unassigned":
                queryset = queryset.filter(assignee__isnull=True)
            else:
                queryset = queryset.filter(assignee_id=assignee)

        # Search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        if connection.schema_name != "public":
            context["users"] = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return context


class TaskDetailView(LoginRequiredMixin, TenantSchemaRequiredMixin, DetailView):
    """Show task details."""

    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self) -> QuerySet[Task]:
        return Task.objects.select_related("project", "assignee").all()


class TaskCreateView(LoginRequiredMixin, TenantSchemaRequiredMixin, CreateView):
    """Create a new task."""

    model = Task
    template_name = "tasks/task_form.html"
    fields = [
        "name",
        "description",
        "project",
        "assignee",
        "status",
        "priority",
        "due_date",
    ]
    success_url = reverse_lazy("task_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        if connection.schema_name != "public":
            assignee_field = cast(ModelChoiceField, form.fields["assignee"])
            assignee_field.queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form

    def form_valid(self, form) -> HttpResponse:
        response: HttpResponse = super().form_valid(form=form)
        messages.success(request=self.request, message="Task created successfully!")
        logger.info(
            "Task created",
            task=form.instance.name,
            task_id=form.instance.pk,
            project_id=form.instance.project.pk,
            assignee_id=form.instance.assignee.pk if form.instance.assignee else None,
            status=form.instance.status,
            priority=form.instance.priority,
            due_date=form.instance.due_date.isoformat()
            if form.instance.due_date
            else None,
            user_id=self.request.user.pk,
        )
        return response


class TaskUpdateView(LoginRequiredMixin, TenantSchemaRequiredMixin, UpdateView):
    """Update an existing task."""

    model = Task
    template_name = "tasks/task_form.html"
    fields = [
        "name",
        "description",
        "project",
        "assignee",
        "status",
        "priority",
        "due_date",
    ]
    success_url = reverse_lazy("task_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        if connection.schema_name != "public":
            assignee_field = cast(ModelChoiceField, form.fields["assignee"])
            assignee_field.queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form

    def form_valid(self, form) -> HttpResponse:
        response: HttpResponse = super().form_valid(form=form)
        messages.success(request=self.request, message="Task updated successfully!")
        logger.info(
            "Task updated",
            task=form.instance.name,
            task_id=form.instance.pk,
            project_id=form.instance.project.pk,
            assignee_id=form.instance.assignee.pk if form.instance.assignee else None,
            status=form.instance.status,
            priority=form.instance.priority,
            due_date=form.instance.due_date.isoformat()
            if form.instance.due_date
            else None,
            user_id=self.request.user.pk,
        )
        return response


class TaskDeleteView(LoginRequiredMixin, TenantSchemaRequiredMixin, DeleteView):
    """Delete a task."""

    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task_list")

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Override post to log the deletion event before the object is deleted.
        """
        self.object = self.get_object()
        task = cast(Task, self.object)
        messages.success(request=self.request, message="Task deleted successfully!")
        logger.info(
            "Task deleted",
            task=task.name,
            task_id=task.pk,
            project_id=task.project.pk,
            user_id=request.user.pk,
        )
        # The parent's post() method calls the original delete().
        return super().post(request=request, *args, **kwargs)

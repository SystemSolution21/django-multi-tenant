# tasks/views.py

# Import django libraries
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Q, QuerySet
from django.db.models.manager import BaseManager
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from rest_framework.viewsets import ModelViewSet

# Import local modules
from tasks.models import Project, Task
from tasks.serializers import ProjectSerializer, TaskSerializer
from tenants.mixins import TenantSchemaRequiredMixin


# ============================================================================
# API ViewSets (REST Framework)
# ============================================================================


class ProjectViewSet(ModelViewSet):
    """
    A viewset for the Project model (API).
    """

    queryset: BaseManager[Project] = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(ModelViewSet):
    """
    A viewset for the Task model (API).
    """

    queryset: BaseManager[Task] = Task.objects.select_related("project").all()
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

    model = Project
    template_name = "tasks/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get tasks for this project
        context["tasks"] = self.object.tasks.select_related("assignee").all()
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
            form.fields["owner"].queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form

    def form_valid(self, form):
        # Set the owner to current user if not specified
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)


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
            form.fields["owner"].queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form


class ProjectDeleteView(LoginRequiredMixin, TenantSchemaRequiredMixin, DeleteView):
    """Delete a project."""

    model = Project
    template_name = "tasks/project_confirm_delete.html"
    success_url = reverse_lazy("project_list")


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
            form.fields["assignee"].queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form


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
            form.fields["assignee"].queryset = User.objects.filter(
                tenants__schema_name=connection.schema_name
            )
        return form


class TaskDeleteView(LoginRequiredMixin, TenantSchemaRequiredMixin, DeleteView):
    """Delete a task."""

    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task_list")

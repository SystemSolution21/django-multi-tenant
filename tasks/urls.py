# tasks/urls.py

# Import standard libraries
from typing import Any

# Import django libraries
from django.urls import path

# Import local modules
from tasks.views import (
    ProjectCreateView,
    ProjectDeleteView,
    ProjectDetailView,
    ProjectListView,
    ProjectUpdateView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskUpdateView,
)

urlpatterns: list[Any] = [
    # Project URLs
    path(route="projects/", view=ProjectListView.as_view(), name="project_list"),
    path(
        route="projects/create/",
        view=ProjectCreateView.as_view(),
        name="project_create",
    ),
    path(
        route="projects/<int:pk>/",
        view=ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path(
        route="projects/<int:pk>/update/",
        view=ProjectUpdateView.as_view(),
        name="project_update",
    ),
    path(
        route="projects/<int:pk>/delete/",
        view=ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    # Task URLs
    path(route="tasks/", view=TaskListView.as_view(), name="task_list"),
    path(route="tasks/create/", view=TaskCreateView.as_view(), name="task_create"),
    path(route="tasks/<int:pk>/", view=TaskDetailView.as_view(), name="task_detail"),
    path(
        route="tasks/<int:pk>/update/",
        view=TaskUpdateView.as_view(),
        name="task_update",
    ),
    path(
        route="tasks/<int:pk>/delete/",
        view=TaskDeleteView.as_view(),
        name="task_delete",
    ),
]


# tasks/views.py

# Import django libraries
from django.db.models.manager import BaseManager
from rest_framework.viewsets import ModelViewSet

# Import local modules
from tasks.models import Project, Task
from tasks.serializers import ProjectSerializer, TaskSerializer


class ProjectViewSet(ModelViewSet):
    """
    A viewset for the Project model.
    """

    queryset: BaseManager[Project] = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(ModelViewSet):
    """
    A viewset for the Task model.
    """

    queryset: BaseManager[Task] = Task.objects.select_related("project").all()
    serializer_class = TaskSerializer

# tasks/serializers.py

# Import django libraries
from rest_framework import serializers

# Import local modules
from tasks.models import Project, Task


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model.
    """

    class Meta:
        model = Project
        fields: list[str] = [
            "id",
            "key",
            "name",
            "description",
            "created_at",
            "updated_at",
        ]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for the Task model.
    """

    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        source="project", queryset=Project.objects.all(), write_only=True
    )

    class Meta:
        model = Task
        fields: list[str] = [
            "id",
            "name",
            "description",
            "project",
            "project_id",
            "is_done",
            "created_at",
            "updated_at",
        ]

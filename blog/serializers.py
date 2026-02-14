# blog/serializers.py

# Import django libraries
from rest_framework import serializers

# Import local modules
from blog.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model.
    """

    class Meta:
        model = Article
        fields: list[str] = [
            "id",
            "title",
            "slug",
            "excerpt",
            "content",
            "status",
            "author",
            "category",
            "tags",
            "created_at",
            "updated_at",
        ]

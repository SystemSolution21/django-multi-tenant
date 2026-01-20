# tenants/serializers.py

# Import django libraries
from rest_framework import serializers

# Import local modules
from tenants.models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tenant model.
    """

    schema_name = serializers.CharField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "schema_name",
            "created_at",
            "updated_at",
        ]

# Generated manually to fix primary key issues

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_user_first_name_user_is_tenant_admin_user_last_name_and_more'),
    ]

    operations = [
        # Drop the existing UserInvitation table completely
        migrations.RunSQL(
            "DROP TABLE IF EXISTS tenants_userinvitation CASCADE;",
            reverse_sql="-- Cannot reverse table drop"
        ),
        
        # Recreate UserInvitation model with UUID primary key from scratch
        migrations.CreateModel(
            name='UserInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('email', models.EmailField(max_length=254)),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('staff', 'Staff'), ('user', 'Regular User')], default='user', max_length=10)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('is_accepted', models.BooleanField(default=False)),
                ('expires_at', models.DateTimeField()),
                ('invited_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='tenants.tenant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='userinvitation',
            unique_together={('tenant', 'email')},
        ),
    ]
# accounts/signals.py

# Import django libraries
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

# Import local modules
from tenants.models import User


@receiver(signal=post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send a welcome email when a new user is created.
    """
    if created and instance.email:
        send_mail(
            subject="Welcome to our SaaS Platform!",
            message=f"Hello {instance.email},\n\nThank you for signing up. We are excited to have you on board!",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            recipient_list=[instance.email],
            fail_silently=True,
        )

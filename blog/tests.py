# blog/tests.py

import logging.config
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django_tenants.utils import get_public_schema_name
from structlog.testing import capture_logs

from .models import Article
from tenants.models import Domain, Tenant

# Hint for static analysis: User is our custom TenantUserModel
User = get_user_model()


class ArticleViewLoggingTest(TestCase):
    """
    Test that user actions in Article views are correctly logged.
    """

    def setUp(self):
        # The Django test runner replaces the logging configuration.
        # We must restore it for structlog's capture_logs to work.
        logging.config.dictConfig(settings.LOGGING)

        # Create a user to be the owner of the public tenant.
        # We can't use create_user before the public tenant exists,
        # so we create the user object manually and set the password.
        owner = User(email="owner@test.com")
        owner.set_password("password123")
        owner.save()

        # Create the public tenant
        public_tenant = Tenant.objects.create(
            schema_name=get_public_schema_name(),
            name="Public Tenant",
            owner=owner,
        )

        # Create the domain for the public tenant
        Domain.objects.create(
            tenant=public_tenant, domain="testserver", is_primary=True
        )

        # Create a regular user for testing actions
        self.user = User.objects.create_user(  # type: ignore
            email="testuser@example.com",
            password="password123",
        )

        # Add the user to the public tenant. This creates the TenantUser (profile) record.
        self.user.tenants.add(public_tenant, through_defaults={"is_active": True})

        self.client.login(email="testuser@example.com", password="password123")

        # Create an article
        self.article = Article.objects.create(
            title="Initial Title", content="Some content."
        )

    def _verify_log_entry(
        self, cap_logs, event_name, user_pk, article_pk, article_title
    ):
        """Helper to find and verify a specific log entry."""
        matching_logs = [log for log in cap_logs if log.get("event") == event_name]
        self.assertEqual(
            len(matching_logs),
            1,
            f"Expected 1 '{event_name}' log, but found {len(matching_logs)}.",
        )

        log = matching_logs[0]
        self.assertEqual(log["user_id"], user_pk)
        self.assertEqual(log["article_id"], article_pk)
        self.assertEqual(log["title"], article_title)

    def test_create_action_is_logged(self):
        """Verify that creating an article creates a log record."""
        create_url = reverse("article_create")
        article_data = {"title": "New Created Article", "content": "Content here."}

        with capture_logs() as cap_logs:
            response = self.client.post(create_url, article_data)

        # Verify the action was successful
        self.assertEqual(response.status_code, 302, "POST should redirect on success.")
        new_article = Article.objects.get(title="New Created Article")

        self._verify_log_entry(
            cap_logs, "article_created", self.user.pk, new_article.pk, new_article.title
        )

    def test_update_action_is_logged(self):
        """Verify that updating an article creates a log record."""
        update_url = reverse("article_update", kwargs={"pk": self.article.pk})
        updated_data = {"title": "Updated Title", "content": "Updated content."}

        with capture_logs() as cap_logs:
            response = self.client.post(update_url, updated_data)

        # Verify the action was successful
        self.assertEqual(response.status_code, 302, "POST should redirect on success.")
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Title")

        self._verify_log_entry(
            cap_logs,
            "article_updated",
            self.user.pk,
            self.article.pk,
            self.article.title,
        )

    def test_delete_action_is_logged(self):
        """Verify that deleting an article creates a log record with the correct context."""
        # self.assertLogs is not compatible with structlog's processor-based logging.
        # The capture_logs context manager correctly captures structlog output.
        delete_url = reverse("article_delete", kwargs={"pk": self.article.pk})
        article_pk = self.article.pk
        article_title = self.article.title

        with capture_logs() as cap_logs:
            response = self.client.post(delete_url)

        # Verify the action was successful
        self.assertEqual(response.status_code, 302, "POST should redirect on success.")
        self.assertFalse(Article.objects.filter(pk=article_pk).exists())

        self._verify_log_entry(
            cap_logs, "article_deleted", self.user.pk, article_pk, article_title
        )

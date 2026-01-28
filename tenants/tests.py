# tenants/tests.py

# Import django libraries
from django.test import TestCase, Client
from django.urls import reverse
from django_tenants.utils import schema_context
from blog.models import Article
from .models import Domain, Tenant, User


class PublicBlogSearchViewTest(TestCase):
    """
    Test the PublicBlogSearchView.
    """

    @classmethod
    def setUpTestData(cls):
        # Create a user to be the owner of the public tenant
        owner = User.objects.create(email="owner@test.com")

        # For django-tenants tests to work, the 'testserver' domain used by the
        # test client must be associated with the public tenant.
        public_tenant, created = Tenant.objects.get_or_create(
            schema_name="public", defaults={"name": "Public Tenant", "owner": owner}
        )
        if not Domain.objects.filter(domain="testserver").exists():
            Domain.objects.create(
                tenant=public_tenant, domain="testserver", is_primary=True
            )

        # Create articles in the public schema once for the test class
        with schema_context("public"):
            Article.objects.create(
                title="Introduction to Django", content="Content for intro..."
            )
            Article.objects.create(
                title="Advanced Django Testing", content="Content for testing..."
            )
            Article.objects.create(
                title="React and Django", content="Content for react..."
            )

    def setUp(self):
        self.client = Client()
        self.url = reverse("public_blog_search")

    def test_search_found(self):
        """Test that searching returns matching articles."""
        response = self.client.get(self.url, {"q": "Django"})
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should find all 3 articles containing "Django"
        # "Introduction to Django", "Advanced Django Testing", "React and Django"
        self.assertEqual(len(data["results"]), 3)

        # Verify structure of the first result
        first_result = data["results"][0]
        self.assertIn("title", first_result)
        self.assertIn("url", first_result)
        self.assertEqual(first_result["type"], "Article")
        # Ensure the URL is relative and points to the blog app
        self.assertTrue(first_result["url"].startswith("/blog/"))

    def test_search_filter(self):
        """Test that search query filters results correctly."""
        response = self.client.get(self.url, {"q": "React"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "React and Django")

    def test_search_min_length(self):
        """Test that queries shorter than 2 characters return no results."""
        response = self.client.get(self.url, {"q": "D"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

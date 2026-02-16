# blog/forms.py

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Div, HTML

from blog.models import Article, Category, Tag


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            "title",
            "slug",
            "excerpt",
            "content",
            "featured_image",
            "status",
            "publish_date",
            "category",
            "tags",
        ]
        widgets = {
            "publish_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # Template handles the form tag

        self.helper.layout = Layout(
            "title",
            "slug",
            "excerpt",
            "content",
            # "featured_image",
            Row(
                Div("status", css_class="col-md-6"),
                Div("publish_date", css_class="col-md-6"),
            ),
            Row(
                Div("category", css_class="col-10"),
                Div(
                    HTML(
                        '<button type="submit" name="action" value="create_category" class="btn btn-outline-secondary w-100" formnovalidate title="Add Category"><i class="bi bi-plus-lg"></i> +</button>'
                    ),
                    css_class="col-2 d-flex align-items-end mb-3",
                ),
            ),
            Row(
                Div("tags", css_class="col-10"),
                Div(
                    HTML(
                        '<button type="submit" name="action" value="create_tag" class="btn btn-outline-secondary w-100" formnovalidate title="Add Tag"><i class="bi bi-plus-lg"></i> +</button>'
                    ),
                    css_class="col-2 d-flex align-items-end mb-3",
                ),
            ),
        )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description"]
        error_messages = {
            "name": {"unique": "A category with this name already exists."}
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["name"]
        error_messages = {"name": {"unique": "A tag with this name already exists."}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

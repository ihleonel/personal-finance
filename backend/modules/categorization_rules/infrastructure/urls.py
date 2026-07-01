from django.urls import path

from .views import (
    CategorizationRuleActivateView,
    CategorizationRuleDeactivateView,
    CategorizationRuleDetailView,
    CategorizationRuleListCreateView,
    SuggestCategoryView,
)


urlpatterns = [
    path(
        "",
        CategorizationRuleListCreateView.as_view(),
        name="categorization-rules-list-create",
    ),
    path(
        "<int:rule_id>/",
        CategorizationRuleDetailView.as_view(),
        name="categorization-rules-detail",
    ),
    path(
        "<int:rule_id>/deactivate/",
        CategorizationRuleDeactivateView.as_view(),
        name="categorization-rules-deactivate",
    ),
    path(
        "<int:rule_id>/activate/",
        CategorizationRuleActivateView.as_view(),
        name="categorization-rules-activate",
    ),
    path(
        "suggest-category/",
        SuggestCategoryView.as_view(),
        name="categorization-rules-suggest-category",
    ),
]
from django.urls import path

from .views import (
    CategoryActivateView,
    CategoryDeactivateView,
    CategoryDetailView,
    CategoryListCreateView,
)


urlpatterns = [
    path("", CategoryListCreateView.as_view(), name="categories-list-create"),
    path("<int:category_id>/", CategoryDetailView.as_view(), name="categories-detail"),
    path(
        "<int:category_id>/deactivate/",
        CategoryDeactivateView.as_view(),
        name="categories-deactivate",
    ),
    path(
        "<int:category_id>/activate/",
        CategoryActivateView.as_view(),
        name="categories-activate",
    ),
]
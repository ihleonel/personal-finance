from django.urls import path

from .views import (
    AccountActivateView,
    AccountBalanceView,
    AccountDeactivateView,
    AccountDetailView,
    AccountListCreateView,
)


urlpatterns = [
    path("", AccountListCreateView.as_view(), name="accounts-list-create"),
    path("<int:account_id>/", AccountDetailView.as_view(), name="accounts-detail"),
    path(
        "<int:account_id>/balance/",
        AccountBalanceView.as_view(),
        name="accounts-balance",
    ),
    path(
        "<int:account_id>/deactivate/",
        AccountDeactivateView.as_view(),
        name="accounts-deactivate",
    ),
    path(
        "<int:account_id>/activate/",
        AccountActivateView.as_view(),
        name="accounts-activate",
    ),
]
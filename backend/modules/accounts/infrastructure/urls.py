from django.urls import path

from .views import AccountDeactivateView, AccountDetailView, AccountListCreateView


urlpatterns = [
    path("", AccountListCreateView.as_view(), name="accounts-list-create"),
    path("<int:account_id>/", AccountDetailView.as_view(), name="accounts-detail"),
    path(
        "<int:account_id>/deactivate/",
        AccountDeactivateView.as_view(),
        name="accounts-deactivate",
    ),
]
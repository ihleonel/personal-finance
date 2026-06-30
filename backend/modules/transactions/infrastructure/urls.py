from django.urls import path

from .views import (
    TransactionImportView,
    TransferCreateView,
    TransactionDetailView,
    TransactionListCreateView,
)


urlpatterns = [
    path("", TransactionListCreateView.as_view(), name="transactions-list-create"),
    path("import/", TransactionImportView.as_view(), name="transactions-import"),
    path("transfer/", TransferCreateView.as_view(), name="transactions-transfer-create"),
    path(
        "<int:transaction_id>/",
        TransactionDetailView.as_view(),
        name="transactions-detail",
    ),
]
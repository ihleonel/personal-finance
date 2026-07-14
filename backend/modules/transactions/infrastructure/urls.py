from django.urls import path

from .views import (
    TransactionAssignByFiltersView,
    TransactionBulkAssignCategoryView,
    TransactionImportView,
    TransferCreateView,
    TransferLinkView,
    TransactionDetailView,
    TransactionListCreateView,
)


urlpatterns = [
    path("", TransactionListCreateView.as_view(), name="transactions-list-create"),
    path("import/", TransactionImportView.as_view(), name="transactions-import"),
    path("transfer/", TransferCreateView.as_view(), name="transactions-transfer-create"),
    path("transfer/link/", TransferLinkView.as_view(), name="transactions-transfer-link"),
    path(
        "bulk-assign-category/",
        TransactionBulkAssignCategoryView.as_view(),
        name="transactions-bulk-assign-category",
    ),
    path(
        "assign-by-filters/",
        TransactionAssignByFiltersView.as_view(),
        name="transactions-assign-by-filters",
    ),
    path(
        "<int:transaction_id>/",
        TransactionDetailView.as_view(),
        name="transactions-detail",
    ),
]
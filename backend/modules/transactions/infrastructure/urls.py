from django.urls import path

from .views import (
    TransactionBulkAssignCategoryView,
    TransactionImportView,
    TransactionDetailView,
    TransactionListCreateView,
)


urlpatterns = [
    path("", TransactionListCreateView.as_view(), name="transactions-list-create"),
    path("import/", TransactionImportView.as_view(), name="transactions-import"),
    path(
        "bulk-assign-category/",
        TransactionBulkAssignCategoryView.as_view(),
        name="transactions-bulk-assign-category",
    ),
    path(
        "<int:transaction_id>/",
        TransactionDetailView.as_view(),
        name="transactions-detail",
    ),
]
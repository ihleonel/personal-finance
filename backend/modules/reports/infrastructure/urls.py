from django.urls import path

from .views import CategorySummaryView, IncomeExpenseSummaryView


urlpatterns = [
    path(
        "income-expense/",
        IncomeExpenseSummaryView.as_view(),
        name="reports-income-expense-summary",
    ),
    path(
        "category-summary/",
        CategorySummaryView.as_view(),
        name="reports-category-summary",
    ),
]
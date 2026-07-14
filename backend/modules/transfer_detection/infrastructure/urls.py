from django.urls import path

from .views import (
    DetectTransfersView,
    SuggestTransferView,
    TransferDetectionRuleActivateView,
    TransferDetectionRuleDeactivateView,
    TransferDetectionRuleDetailView,
    TransferDetectionRuleListCreateView,
)


urlpatterns = [
    path(
        "",
        TransferDetectionRuleListCreateView.as_view(),
        name="transfer-detection-rules-list-create",
    ),
    path(
        "<int:rule_id>/",
        TransferDetectionRuleDetailView.as_view(),
        name="transfer-detection-rules-detail",
    ),
    path(
        "<int:rule_id>/deactivate/",
        TransferDetectionRuleDeactivateView.as_view(),
        name="transfer-detection-rules-deactivate",
    ),
    path(
        "<int:rule_id>/activate/",
        TransferDetectionRuleActivateView.as_view(),
        name="transfer-detection-rules-activate",
    ),
    path(
        "suggest/",
        SuggestTransferView.as_view(),
        name="transfer-detection-suggest",
    ),
    path(
        "detect/",
        DetectTransfersView.as_view(),
        name="transfer-detection-detect",
    ),
]
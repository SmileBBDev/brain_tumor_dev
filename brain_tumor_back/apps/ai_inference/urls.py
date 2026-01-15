from django.urls import path
from .views import (
    M1InferenceView,
    MGInferenceView,
    MMInferenceView,
    MMAvailableOCSView,
    InferenceCallbackView,
    AIInferenceListView,
    AIInferenceDetailView,
    AIInferenceDeleteByOCSView,
    AIInferenceFileDownloadView,
    AIInferenceFilesListView,
    AIInferenceSegmentationView,
    MGGeneExpressionView,
)

app_name = 'ai_inference'

urlpatterns = [
    # M1 inference
    path('m1/inference/', M1InferenceView.as_view(), name='m1-inference'),

    # MG inference
    path('mg/inference/', MGInferenceView.as_view(), name='mg-inference'),
    path('mg/gene-expression/<int:ocs_id>/', MGGeneExpressionView.as_view(), name='mg-gene-expression'),

    # MM inference (Multimodal)
    path('mm/inference/', MMInferenceView.as_view(), name='mm-inference'),
    path('mm/available-ocs/<str:patient_id>/', MMAvailableOCSView.as_view(), name='mm-available-ocs'),

    # Callback (shared)
    path('callback/', InferenceCallbackView.as_view(), name='callback'),

    # Inference list/detail
    path('inferences/', AIInferenceListView.as_view(), name='inference-list'),
    path('inferences/by-ocs/<int:ocs_id>/', AIInferenceDeleteByOCSView.as_view(), name='inference-delete-by-ocs'),
    path('inferences/<str:job_id>/', AIInferenceDetailView.as_view(), name='inference-detail'),

    # Files
    path('inferences/<str:job_id>/files/', AIInferenceFilesListView.as_view(), name='inference-files'),
    path('inferences/<str:job_id>/files/<str:filename>/', AIInferenceFileDownloadView.as_view(), name='inference-file-download'),

    # Segmentation data
    path('inferences/<str:job_id>/segmentation/', AIInferenceSegmentationView.as_view(), name='inference-segmentation'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIModelViewSet,
    AIInferenceRequestViewSet,
    AIInferenceResultViewSet,
    PatientAIViewSet
)

router = DefaultRouter()
router.register(r'models', AIModelViewSet, basename='ai-models')
router.register(r'requests', AIInferenceRequestViewSet, basename='ai-requests')
router.register(r'results', AIInferenceResultViewSet, basename='ai-results')

urlpatterns = [
    path('', include(router.urls)),
    # 환자별 AI 조회
    path('patients/<int:pk>/requests/', PatientAIViewSet.as_view({'get': 'requests'}), name='patient-ai-requests'),
    path('patients/<int:pk>/available-models/', PatientAIViewSet.as_view({'get': 'available_models'}), name='patient-available-models'),
]

"""
FHIR URLs

FHIR 리소스 조회 및 동기화 API 라우팅
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FHIRResourceMapViewSet,
    FHIRSyncQueueViewSet,
    get_patient_fhir,
    get_encounter_fhir,
    get_observation_fhir,
    get_diagnostic_report_fhir,
    get_medication_request_fhir,
    get_service_request_fhir,
    get_condition_fhir,
    get_imaging_study_fhir,
    get_procedure_fhir,
    get_procedure_fhir,
    create_fhir_sync_task,
    fhir_proxy
)

# Router 설정
router = DefaultRouter()
router.register(r'resource-maps', FHIRResourceMapViewSet, basename='fhir-resource-map')
router.register(r'sync-queue', FHIRSyncQueueViewSet, basename='fhir-sync-queue')

urlpatterns = [
    # Router URLs (ViewSets)
    path('', include(router.urls)),

    # FHIR 리소스 조회 엔드포인트 (기본 4개)
    path('Patient/<str:patient_id>/', get_patient_fhir, name='fhir-patient'),
    path('Encounter/<str:encounter_id>/', get_encounter_fhir, name='fhir-encounter'),
    path('Observation/<str:result_id>/', get_observation_fhir, name='fhir-observation'),
    path('DiagnosticReport/<int:job_id>/', get_diagnostic_report_fhir, name='fhir-diagnostic-report'),

    # FHIR 리소스 조회 엔드포인트 (추가 5개)
    path('MedicationRequest/<str:order_id>/', get_medication_request_fhir, name='fhir-medication-request'),
    path('ServiceRequest/<str:order_id>/', get_service_request_fhir, name='fhir-service-request'),
    path('Condition/<int:diagnosis_id>/', get_condition_fhir, name='fhir-condition'),
    path('ImagingStudy/<str:study_id>/', get_imaging_study_fhir, name='fhir-imaging-study'),
    path('Procedure/<str:order_id>/', get_procedure_fhir, name='fhir-procedure'),

    # FHIR 동기화 작업 생성
    path('sync/', create_fhir_sync_task, name='fhir-sync-create'),

    # FHIR Proxy (Metadata, Search 등) - 가장 마지막에 배치
    path('proxy/<path:path>', fhir_proxy, name='fhir-proxy'),
]

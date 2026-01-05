from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_htj2k_comparison

router = DefaultRouter()
router.register(r'orders', views.RadiologyOrderViewSet, basename='radiology-order')
router.register(r'studies', views.RadiologyStudyViewSet, basename='radiology-study')
router.register(r'reports', views.RadiologyReportViewSet, basename='radiology-report')

urlpatterns = [
    path('health/', views.orthanc_health_check, name='orthanc-health'),
    path('auth-check/', views.auth_check, name='auth-check'),
    path('sync/', views.sync_orthanc_studies, name='sync-orthanc-studies'),
    path('upload/dicom/', views.DicomUploadView.as_view(), name='dicom-upload'),

    # --- Proxy Routes ---
    path('pacs/dicom-web/<path:path>', views.dicom_web_proxy, name='dicom-web-proxy'),
    path('viewer/', views.ohif_viewer_index, name='ohif-viewer-index'),
    path('viewer/<path:path>', views.ohif_viewer_proxy, name='ohif-viewer-proxy'),
    path('wado', views.wado_proxy, name='wado-proxy'),

    # Orthanc 연동 테스트 API
    path('test/patients/', views.test_orthanc_patients, name='test-orthanc-patients'),
    path('test/studies/', views.test_orthanc_studies, name='test-orthanc-studies'),

    # HTJ2K 압축 비교 UI 및 API
    path('htj2k/comparison/', views_htj2k_comparison.htj2k_comparison_page, name='htj2k-comparison-page'),
    path('htj2k/patients/', views_htj2k_comparison.get_patients_for_comparison, name='htj2k-patients'),
    path('htj2k/patients/<str:patient_id>/studies/', views_htj2k_comparison.get_patient_studies, name='htj2k-patient-studies'),
    path('htj2k/studies/<str:study_id>/instances/', views_htj2k_comparison.get_study_instances, name='htj2k-study-instances'),
    path('htj2k/studies/<str:study_id>/statistics/', views_htj2k_comparison.get_study_statistics, name='htj2k-study-statistics'),
    path('htj2k/instances/<str:instance_id>/download/standard/', views_htj2k_comparison.download_dicom_standard, name='htj2k-download-standard'),
    path('htj2k/instances/<str:instance_id>/download/htj2k/', views_htj2k_comparison.download_dicom_htj2k_simulated, name='htj2k-download-htj2k'),

    path('', include(router.urls)),
]

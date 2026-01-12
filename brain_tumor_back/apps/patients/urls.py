from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # 환자 목록 및 등록
    path('', views.patient_list_create, name='patient-list-create'),

    # 환자 상세, 수정, 삭제
    path('<int:patient_id>/', views.patient_detail, name='patient-detail'),

    # 환자 요약서 (PDF 생성용)
    path('<int:patient_id>/summary/', views.patient_summary, name='patient-summary'),

    # 환자 진찰 요약 (ExaminationTab용)
    path('<int:patient_id>/examination-summary/', views.patient_examination_summary, name='patient-examination-summary'),

    # 환자 주의사항
    path('<int:patient_id>/alerts/', views.patient_alerts_list_create, name='patient-alerts-list-create'),
    path('<int:patient_id>/alerts/<int:alert_id>/', views.patient_alert_detail, name='patient-alert-detail'),

    # 환자 검색 (자동완성용)
    path('search/', views.patient_search, name='patient-search'),

    # 환자 통계
    path('statistics/', views.patient_statistics, name='patient-statistics'),

    # 외부 환자 등록 (EXTR_XXXX 형식)
    path('create_external/', views.create_external_patient, name='patient-create-external'),
]

from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # 환자 목록 및 등록
    path('', views.patient_list_create, name='patient-list-create'),
    
    # 환자 상세, 수정, 삭제
    path('<int:patient_id>/', views.patient_detail, name='patient-detail'),
    
    # 환자 검색 (자동완성용)
    path('search/', views.patient_search, name='patient-search'),
    
    # 환자 통계
    path('statistics/', views.patient_statistics, name='patient-statistics'),
]

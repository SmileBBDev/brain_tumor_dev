from datetime import datetime
from django.utils import timezone
from .clients import OrthancClient
from .models import RadiologyOrder, RadiologyStudy, RadiologyReport


class RadiologyOrderService:
    @staticmethod
    def create_order(data, user):
        """영상 검사 오더 생성"""
        # 비즈니스 로직: 유효성 검사, 상태 초기화 등
        order = RadiologyOrder.objects.create(
            ordered_by=user,
            **data
        )
        return order

    @staticmethod
    def update_status(order_id, status):
        """오더 상태 변경"""
        order = RadiologyOrder.objects.get(order_id=order_id)
        order.status = status
        order.save()
        return order


class RadiologyStudyService:
    def __init__(self):
        self.client = OrthancClient()

    def sync_studies_from_orthanc(self, limit=50):
        orthanc_studies = self.client.get_studies(limit=limit)
        
        synced_count = 0
        for orthanc_study_id in orthanc_studies:
            try:
                # Orthanc Study 상세 정보 조회
                study_data = self.client.get_study(orthanc_study_id)
                metadata = self.client.get_study_metadata(orthanc_study_id)
                
                # DICOM 메타데이터 파싱 (fallback to study-level tags if simplified-tags empty)
                main_tags = study_data.get('MainDicomTags', {})
                patient_tags = study_data.get('PatientMainDicomTags', {})
                
                patient_name = metadata.get('PatientName') or patient_tags.get('PatientName', 'Unknown')
                patient_id = metadata.get('PatientID') or patient_tags.get('PatientID', 'Unknown')
                study_date_str = metadata.get('StudyDate') or main_tags.get('StudyDate', '')
                study_time_str = metadata.get('StudyTime') or main_tags.get('StudyTime', '')
                study_instance_uid = metadata.get('StudyInstanceUID') or main_tags.get('StudyInstanceUID', orthanc_study_id)
                
                # 날짜/시간 변환
                study_date = None
                study_time = None
                if study_date_str:
                    try:
                        study_date = datetime.strptime(study_date_str, '%Y%m%d').date()
                    except ValueError:
                        pass
                if study_time_str:
                    try:
                        # DICOM 시간 형식: HHMMSS.ffffff
                        time_parts = study_time_str.split('.')[0]
                        study_time = datetime.strptime(time_parts, '%H%M%S').time()
                    except ValueError:
                        pass
                
                # 환자 매칭 (PatientCache 조회)
                from emr.models import PatientCache
                from django.db.models import Q
                
                # 1. Exact ID Match
                matched_patient = PatientCache.objects.filter(patient_id=patient_id).first()
                
                # 2. Substring Match (e.g., '0005' in 'P-2025-005' -> try lstrip zeros)
                if not matched_patient and patient_id != 'Unknown':
                    # Try exact match, then icontains, then stripped match
                    matched_patient = PatientCache.objects.filter(patient_id__icontains=patient_id).first()
                    if not matched_patient:
                        # '0005' -> '5', then search for '5' in 'P-2025-005'
                        short_id = patient_id.lstrip('0')
                        if short_id:
                            matched_patient = PatientCache.objects.filter(patient_id__icontains=short_id).first()
                
                # 3. Name Match (fallback) - try matching '0005' from 'sub-0005'
                if not matched_patient and patient_name != 'Unknown':
                    search_name = patient_name.replace('^', ' ').strip()
                    # Also try matching sub-0005 numeric part to patient_id
                    import re
                    numeric_part = re.search(r'\d+', search_name)
                    if numeric_part:
                        short_num = numeric_part.group().lstrip('0')
                        if short_num:
                            matched_patient = PatientCache.objects.filter(patient_id__icontains=short_num).first()
                    
                    if not matched_patient:
                        matched_patient = PatientCache.objects.filter(
                            Q(family_name__icontains=search_name) | 
                            Q(given_name__icontains=search_name)
                        ).first()
                # 또는 주민번호/이름으로 2차 매칭 시도 가능 (현재는 ID 매칭만)
                
                # Django DB에 저장/업데이트
                RadiologyStudy.objects.update_or_create(
                    orthanc_study_id=orthanc_study_id,
                    defaults={
                        'study_instance_uid': study_instance_uid,
                        'patient_name': patient_name,
                        'patient': matched_patient,     # Matched FK (uses 'patient_id' column)
                        'study_date': study_date,
                        'study_time': study_time,
                        'study_description': metadata.get('StudyDescription', ''),
                        'modality': metadata.get('Modality', ''),
                        'referring_physician': metadata.get('ReferringPhysicianName', ''),
                        'num_series': len(study_data.get('Series', [])),
                        'num_instances': len(study_data.get('Instances', [])),
                    }
                )
                synced_count += 1
            except Exception as e:
                print(f"Failed to sync study {orthanc_study_id}: {e}")
                continue
                
        return {
            'synced_count': synced_count,
            'total': len(orthanc_studies)
        }

class RadiologyReportService:
    def sign_report(self, report_id, user):
        from .models import RadiologyReport
        from django.utils import timezone
        
        report = RadiologyReport.objects.get(report_id=report_id)
        
        if report.status == 'FINAL':
            raise ValueError('Report already finalized')
            
        report.status = 'FINAL'
        report.signed_at = timezone.now()
        report.signed_by = user
        report.save()
        
        return report

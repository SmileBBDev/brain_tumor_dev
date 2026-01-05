
from django.db import transaction, connections
from datetime import datetime
from .models import PatientCache, Encounter, Order, OrderItem
from .openemr_models import (
    PatientData as OpenEMRPatientData,
    Encounter as OpenEMRRemoteEncounter,
    Form as OpenEMRForm,
    Prescription as OpenEMRPrescription
)


class OpenEMRPatientRepository:
    """OpenEMR patient_data 테이블 직접 접근"""

    @staticmethod
    def create_patient_in_openemr(data):
        """
        OpenEMR patient_data 테이블에 환자 등록 (Using Django ORM Router)

        Args:
            data: PatientCache 모델에서 변환된 환자 데이터

        Returns:
            생성된 OpenEMR pid (int)
        """
        # 1. Manual PID Generation
        # OpenEMR의 pid 컬럼이 AI(Auto Increment)가 아닐 수 있으므로 직접 MAX값 조회
        from django.db.models import Max
        current_max_pid = OpenEMRPatientData.objects.aggregate(Max('pid'))['pid__max'] or 0
        new_pid = current_max_pid + 1

        # 2. 필수 필드 매핑 (Django PatientCache -> OpenEMR patient_data)
        
        # 주소 파싱 (address 필드를 street, city, state로 분리)
        address_parts = data.get('address', '').split(',')
        street = address_parts[0].strip() if len(address_parts) > 0 else ''
        city = address_parts[1].strip() if len(address_parts) > 1 else ''
        state = address_parts[2].strip() if len(address_parts) > 2 else ''

        # 성별 변환 (male/female -> Male/Female)
        sex = data.get('gender', 'male').capitalize()

        # ORM을 통한 생성
        patient_data = OpenEMRPatientData.objects.create(
            id=new_pid,
            pid=new_pid,
            pubpid=data.get('patient_id', ''),
            
            fname=data.get('given_name', ''),
            lname=data.get('family_name', ''),
            mname='',
            DOB=data.get('birth_date'),
            sex=sex,
            
            street=street,
            city=city,
            state=state,
            postal_code='',
            country_code='KR',
            
            phone_home=data.get('phone', ''),
            phone_cell=data.get('phone', ''),
            email=data.get('email', ''),
            
            # regdate, last_updated are handled by auto_now_add/auto_now
            
            title='',
            language='korean',
            financial='',
            status='active',
            
            hipaa_mail='YES',
            hipaa_voice='YES',
            hipaa_notice='YES',
            hipaa_message='',
            hipaa_allowsms='YES',
            hipaa_allowemail='YES',
            
            allow_patient_portal='YES',
            dupscore=-9
        )

        return new_pid



    @staticmethod
    def get_patient_by_pubpid(pubpid):
        """
        pubpid로 OpenEMR 환자 조회 (Using Django ORM Router)

        Args:
            pubpid: Django patient_id (P-YYYY-NNNNNN)

        Returns:
            환자 정보 dict 또는 None
        """
        patient = OpenEMRPatientData.objects.filter(pubpid=pubpid).first()
        
        if patient:
            return {
                'pid': patient.pid,
                'fname': patient.fname,
                'lname': patient.lname,
                'DOB': patient.DOB,
                'sex': patient.sex,
                'email': patient.email,
                'phone_home': patient.phone_home,
                'pubpid': patient.pubpid,
            }
        return None

    @staticmethod
    def update_patient_in_openemr(pid, data):
        """
        OpenEMR patient_data 업데이트 (Using Django ORM Router)
        """
        updated_count = OpenEMRPatientData.objects.filter(pid=pid).update(
            fname=data.get('given_name', ''),
            lname=data.get('family_name', ''),
            DOB=data.get('birth_date'),
            # 필요한 필드만 업데이트
            phone_home=data.get('phone', ''),
            phone_cell=data.get('phone', ''),
            email=data.get('email', '')
        )
        return updated_count > 0

    @staticmethod
    def delete_patient_in_openemr(pid):
        """
        OpenEMR patient_data 삭제 (Using Django ORM Router)
        """
        # 실제 삭제 대신 status를 inactive로 변경하거나 할 수 있으나
        # 여기서는 레거시 동작에 맞춰 삭제를 시도하거나 status 변경
        # 여기서는 예제상 status 변경으로 처리
        return OpenEMRPatientData.objects.filter(pid=pid).update(status='inactive') > 0


class OpenEMREncounterRepository:
    """OpenEMR encounters 및 forms 테이블 직접 접근"""

    @staticmethod
    def create_encounter_in_openemr(data):
        """
        OpenEMR에 진료기록 등록 (Using Django ORM Router)
        """
        patient_id = data.get('patient')
        if hasattr(patient_id, 'patient_id'):
            patient_id = patient_id.patient_id
        
        patient_info = OpenEMRPatientRepository.get_patient_by_pubpid(str(patient_id))
        if not patient_info:
            raise Exception(f"OpenEMR에서 환자를 찾을 수 없습니다: {patient_id}")
        
        pid = patient_info['pid']
        now = datetime.now()

        # 1. encounters 테이블 insert
        # OpenEMR encounters 테이블은 보통 encounter_id가 자동 생성되거나 id로 관리됨
        from django.db.models import Max
        current_max_enc = OpenEMRRemoteEncounter.objects.filter(pid=pid).aggregate(Max('encounter'))['encounter__max'] or 0
        new_enc_no = current_max_enc + 1

        OpenEMRRemoteEncounter.objects.create(
            date=now,
            reason=data.get('chief_complaint', ''),
            facility_id=1,
            pid=pid,
            encounter=new_enc_no,
            last_level_all=0,
            last_level_closed=0
        )
        
        # 2. forms 테이블 (진료 기록의 메타데이터)
        OpenEMRForm.objects.create(
            date=now,
            encounter=new_enc_no,
            form_name='New Patient Encounter',
            form_id=new_enc_no,
            pid=pid,
            user='admin',
            groupname='Default',
            authorized=1
        )
        
        return new_enc_no


class PatientRepository:
    """환자 데이터 저장소"""

    @staticmethod
    def create_patient(data):
        """환자 생성"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating patient in Django DB: {data.get('patient_id')} - {data.get('family_name')}")
        
        patient_id = data.pop('patient_id', None)
        try:
            patient = PatientCache.objects.create(patient_id=patient_id, **data)
            logger.info(f"Successfully created patient {patient_id}")
            return patient
        except Exception as e:
            logger.error(f"Error creating patient {patient_id} in Django DB: {str(e)}")
            raise e

    @staticmethod
    def get_patient_by_id(patient_id, for_update=False):
        """환자 조회 (for_update 옵션 추가)"""
        queryset = PatientCache.objects.filter(patient_id=patient_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_patient(patient_id, data):
        """환자 정보 단순 업데이트"""
        rows_updated = PatientCache.objects.filter(patient_id=patient_id).update(**data)
        return rows_updated > 0

    @staticmethod
    def update_patient_optimistic(patient_id, old_version, data):
        """낙관적 락을 이용한 환자 정보 업데이트"""
        from django.db.models import F
        rows_updated = PatientCache.objects.filter(
            patient_id=patient_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

    @staticmethod
    def get_last_patient_by_year(year):
        """해당 연도의 마지막 환자 조회 (Deprecated: String Sort Issue)"""
        return PatientCache.objects.filter(
            patient_id__startswith=f'P-{year}-'
        ).order_by('-patient_id').first()

    @staticmethod
    def get_max_patient_sequence(year):
        """
        해당 연도의 가장 큰 시퀀스 번호 반환 (포맷 혼용 대응)
        예: P-2025-030 (3자리) vs P-2025-000031 (6자리) 문자열 정렬 문제 해결
        """
        prefix = f'P-{year}-'
        # 모든 ID를 가져와서 숫자 부분만 파싱하여 최대값 계산 (데이터량이 많지 않다고 가정)
        patients = PatientCache.objects.filter(patient_id__startswith=prefix).values_list('patient_id', flat=True)
        
        max_seq = 0
        for pid in patients:
            try:
                parts = pid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
                
        return max_seq


class EncounterRepository:
    """진료 기록 데이터 저장소"""

    @staticmethod
    def create_encounter(data):
        """진료 기록 생성"""
        return Encounter.objects.create(**data)

    @staticmethod
    def get_encounter_by_id(encounter_id, for_update=False):
        """진료 기록 조회 (for_update 옵션 추가)"""
        queryset = Encounter.objects.filter(encounter_id=encounter_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_encounter_optimistic(encounter_id, old_version, data):
        """낙관적 락을 이용한 진료 기록 업데이트"""
        from django.db.models import F
        rows_updated = Encounter.objects.filter(
            encounter_id=encounter_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

    @staticmethod
    def get_max_encounter_sequence(year):
        """해당 연도 진료기록 Max Sequence 조회"""
        prefix = f'E-{year}-'
        # 모든 ID 조회 후 메모리에서 Max 계산 (데이터량 적음 가정)
        encounters = Encounter.objects.filter(encounter_id__startswith=prefix).values_list('encounter_id', flat=True)
        
        max_seq = 0
        for eid in encounters:
            try:
                parts = eid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
        return max_seq


class OrderRepository:
    """처방 데이터 저장소"""

    @staticmethod
    def create_order(order_data, items_data):
        """처방 및 처방 항목 생성 (Transaction 보장)"""
        with transaction.atomic():
            order = Order.objects.create(**order_data)

            for item_datum in items_data:
                OrderItem.objects.create(order=order, **item_datum)

            return order

    @staticmethod
    def get_order_by_id(order_id, for_update=False):
        """처방 조회 (for_update 옵션 추가)"""
        queryset = Order.objects.filter(order_id=order_id)
        if for_update:
            queryset = queryset.select_for_update()
        return queryset.first()

    @staticmethod
    def update_order_optimistic(order_id, old_version, data):
        """낙관적 락을 이용한 처방 업데이트"""
        from django.db.models import F
        rows_updated = Order.objects.filter(
            order_id=order_id, 
            version=old_version
        ).update(**data, version=F('version') + 1)
        return rows_updated > 0

    @staticmethod
    def get_max_order_sequence(year):
        """해당 연도 처방 Max Sequence 조회"""
        prefix = f'O-{year}-'
        orders = Order.objects.filter(order_id__startswith=prefix).values_list('order_id', flat=True)
        
        max_seq = 0
        for oid in orders:
            try:
                parts = oid.split('-')
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except ValueError:
                continue
        return max_seq


class OpenEMROrderRepository:
    """OpenEMR prescriptions 테이블 직접 접근"""

    @staticmethod
    def create_prescription_in_openemr(order_data, items_data):
        """
        OpenEMR prescriptions 테이블에 처방 등록 (Using Django ORM Router)
        
        Args:
            order_data: Order 생성을 위한 딕셔너리 (patient_id 포함 필수)
            items_data: OrderItem 생성을 위한 딕셔너리 리스트
        
        Returns:
            list[int]: 생성된 OpenEMR prescription id 목록 (필요시)
        """
        # 1. 환자의 OpenEMR pid 조회
        # order_data에는 'patient'가 객체일 수도 있고 ID 문자열일 수도 있음
        # 여기서는 patient_id 문자열을 우선 사용
        patient_ref = order_data.get('patient')
        if hasattr(patient_ref, 'patient_id'):
            patient_id_str = patient_ref.patient_id
        else:
            patient_id_str = str(patient_ref)

        patient_info = OpenEMRPatientRepository.get_patient_by_pubpid(patient_id_str)
        if not patient_info:
            raise Exception(f"OpenEMR에서 환자를 찾을 수 없습니다. (Patient ID: {patient_id_str})")
        
        pid = patient_info['pid']
        now = datetime.now()

        created_ids = []

        # 2. 각 처방 항목을 prescriptions 테이블에 Insert (ORM)
        for item in items_data:
            # item이 객체인지 딕셔너리인지 확인
            drug_name = getattr(item, 'drug_name', item.get('drug_name'))
            dosage = getattr(item, 'dosage', item.get('dosage'))

            prescription = OpenEMRPrescription.objects.create(
                patient_id=pid,
                drug=drug_name,
                dosage=dosage,
                quantity=1,
                refills=0,
                start_date=now.date(),
                # date_added, date_modified handled by auto_now
                provider_id=1,
                active=1,
                txDate=now.date(),
                usage_category_title='',
                request_intent_title=''
            )
            created_ids.append(prescription.id)

        return created_ids


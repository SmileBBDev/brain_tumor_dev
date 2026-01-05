"""
마스터 데이터 시딩 Management Command

사용법:
    python manage.py seed_master_data
    python manage.py seed_master_data --diagnosis-only
    python manage.py seed_master_data --medication-only
    python manage.py seed_master_data --labtest-only
    python manage.py seed_master_data --force  # 기존 데이터 덮어쓰기

작성일: 2025-12-30
목적: 진단(ICD-10), 약물, 검사 마스터 데이터를 DB에 업로드
"""
import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ocs.models import DiagnosisMaster, MedicationMaster
from lis.models import LabTestMaster


class Command(BaseCommand):
    help = '마스터 데이터(진단/약물/검사)를 데이터베이스에 시딩합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--diagnosis-only',
            action='store_true',
            help='진단 마스터 데이터만 시딩'
        )
        parser.add_argument(
            '--medication-only',
            action='store_true',
            help='약물 마스터 데이터만 시딩'
        )
        parser.add_argument(
            '--labtest-only',
            action='store_true',
            help='검사 마스터 데이터만 시딩'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 데이터를 덮어씁니다 (update_or_create 사용)'
        )

    def handle(self, *args, **options):
        """Command 실행 진입점"""
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("[START] Master Data Seeding Started"))
        self.stdout.write("=" * 80)

        # 플래그 확인
        diagnosis_only = options['diagnosis_only']
        medication_only = options['medication_only']
        labtest_only = options['labtest_only']
        force = options['force']

        # 플래그가 없으면 모두 시딩
        seed_all = not (diagnosis_only or medication_only or labtest_only)

        # 통계 초기화
        total_stats = {
            'diagnosis': {'created': 0, 'updated': 0, 'errors': 0},
            'medication': {'created': 0, 'updated': 0, 'errors': 0},
            'labtest': {'created': 0, 'updated': 0, 'errors': 0},
        }

        # 진단 마스터 시딩
        if diagnosis_only or seed_all:
            self.stdout.write("\n[DIAGNOSIS] Seeding diagnosis master data...")
            stats = self._seed_diagnosis(force)
            total_stats['diagnosis'] = stats

        # 약물 마스터 시딩
        if medication_only or seed_all:
            self.stdout.write("\n[MEDICATION] Seeding medication master data...")
            stats = self._seed_medication(force)
            total_stats['medication'] = stats

        # 검사 마스터 시딩
        if labtest_only or seed_all:
            self.stdout.write("\n[LABTEST] Seeding lab test master data...")
            stats = self._seed_labtest(force)
            total_stats['labtest'] = stats

        # 최종 통계 출력
        self._print_final_stats(total_stats)

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("[SUCCESS] Master Data Seeding Completed"))
        self.stdout.write("=" * 80)

    def _seed_diagnosis(self, force):
        """진단 마스터 데이터 시딩 (ICD-10 기반)"""
        stats = {'created': 0, 'updated': 0, 'errors': 0}

        # 기존 스크립트에서 진단 데이터 가져오기
        diagnosis_data = self._get_diagnosis_data()

        for data in diagnosis_data:
            try:
                with transaction.atomic():
                    if force:
                        # 덮어쓰기 모드
                        diagnosis, created = DiagnosisMaster.objects.update_or_create(
                            diag_code=data['diag_code'],
                            defaults={
                                'name_ko': data['name_ko'],
                                'name_en': data['name_en'],
                                'category': data['category'],
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['diag_code']} - {data['name_ko']}"
                                )
                            )
                        else:
                            stats['updated'] += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  [UPDATED] {data['diag_code']} - {data['name_ko']}"
                                )
                            )
                    else:
                        # 없을 때만 추가
                        diagnosis, created = DiagnosisMaster.objects.get_or_create(
                            diag_code=data['diag_code'],
                            defaults={
                                'name_ko': data['name_ko'],
                                'name_en': data['name_en'],
                                'category': data['category'],
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['diag_code']} - {data['name_ko']}"
                                )
                            )
                        else:
                            self.stdout.write(
                                f"  [SKIP] {data['diag_code']} - {data['name_ko']} (already exists)"
                            )

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] {data['diag_code']} - {data['name_ko']} - {str(e)}"
                    )
                )

        return stats

    def _seed_medication(self, force):
        """약물 마스터 데이터 시딩"""
        stats = {'created': 0, 'updated': 0, 'errors': 0}

        # JSON 파일 경로
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_file = base_dir / 'data' / 'medication_master.json'

        if not json_file.exists():
            self.stdout.write(
                self.style.ERROR(f"  [ERROR] File not found: {json_file}")
            )
            return stats

        # JSON 파일 읽기
        with open(json_file, 'r', encoding='utf-8') as f:
            medication_data = json.load(f)

        for data in medication_data:
            try:
                with transaction.atomic():
                    if force:
                        medication, created = MedicationMaster.objects.update_or_create(
                            drug_code=data['drug_code'],
                            defaults={
                                'drug_name': data['drug_name'],
                                'generic_name': data.get('generic_name'),
                                'dosage_form': data.get('dosage_form'),
                                'strength': data.get('strength'),
                                'unit': data.get('unit'),
                                'manufacturer': data.get('manufacturer'),
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['drug_code']} - {data['drug_name']}"
                                )
                            )
                        else:
                            stats['updated'] += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  [UPDATED] {data['drug_code']} - {data['drug_name']}"
                                )
                            )
                    else:
                        medication, created = MedicationMaster.objects.get_or_create(
                            drug_code=data['drug_code'],
                            defaults={
                                'drug_name': data['drug_name'],
                                'generic_name': data.get('generic_name'),
                                'dosage_form': data.get('dosage_form'),
                                'strength': data.get('strength'),
                                'unit': data.get('unit'),
                                'manufacturer': data.get('manufacturer'),
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['drug_code']} - {data['drug_name']}"
                                )
                            )
                        else:
                            self.stdout.write(
                                f"  [SKIP] {data['drug_code']} - {data['drug_name']} (already exists)"
                            )

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] {data['drug_code']} - {data['drug_name']} - {str(e)}"
                    )
                )

        return stats

    def _seed_labtest(self, force):
        """검사 마스터 데이터 시딩"""
        stats = {'created': 0, 'updated': 0, 'errors': 0}

        # JSON 파일 경로
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_file = base_dir / 'data' / 'lab_test_master.json'

        if not json_file.exists():
            self.stdout.write(
                self.style.ERROR(f"  [ERROR] File not found: {json_file}")
            )
            return stats

        # JSON 파일 읽기
        with open(json_file, 'r', encoding='utf-8') as f:
            labtest_data = json.load(f)

        for data in labtest_data:
            try:
                with transaction.atomic():
                    if force:
                        labtest, created = LabTestMaster.objects.update_or_create(
                            test_code=data['test_code'],
                            defaults={
                                'test_name': data['test_name'],
                                'sample_type': data.get('sample_type'),
                                'method': data.get('method'),
                                'unit': data.get('unit'),
                                'reference_range': data.get('reference_range'),
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['test_code']} - {data['test_name']}"
                                )
                            )
                        else:
                            stats['updated'] += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  [UPDATED] {data['test_code']} - {data['test_name']}"
                                )
                            )
                    else:
                        labtest, created = LabTestMaster.objects.get_or_create(
                            test_code=data['test_code'],
                            defaults={
                                'test_name': data['test_name'],
                                'sample_type': data.get('sample_type'),
                                'method': data.get('method'),
                                'unit': data.get('unit'),
                                'reference_range': data.get('reference_range'),
                                'is_active': True
                            }
                        )
                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  [CREATED] {data['test_code']} - {data['test_name']}"
                                )
                            )
                        else:
                            self.stdout.write(
                                f"  [SKIP] {data['test_code']} - {data['test_name']} (already exists)"
                            )

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] {data['test_code']} - {data['test_name']} - {str(e)}"
                    )
                )

        return stats

    def _get_diagnosis_data(self):
        """진단 마스터 데이터 반환 (add_diagnosis_data.py에서 가져옴)"""
        # 기존 add_diagnosis_data.py의 diagnosis_data 그대로 사용
        return [
            # === 뇌 질환 (G00-G99: 신경계통의 질환) ===
            # 뇌혈관 질환
            {"diag_code": "I60.0", "name_ko": "비외상성 지주막하출혈", "name_en": "Subarachnoid hemorrhage", "category": "뇌혈관질환"},
            {"diag_code": "I61.0", "name_ko": "뇌내출혈", "name_en": "Intracerebral hemorrhage", "category": "뇌혈관질환"},
            {"diag_code": "I63.0", "name_ko": "뇌경색증", "name_en": "Cerebral infarction", "category": "뇌혈관질환"},
            {"diag_code": "I64", "name_ko": "출혈 또는 경색으로 명시되지 않은 뇌졸중", "name_en": "Stroke, not specified", "category": "뇌혈관질환"},
            {"diag_code": "G45.0", "name_ko": "일과성 뇌허혈발작", "name_en": "Transient cerebral ischemic attack", "category": "뇌혈관질환"},

            # 뇌종양
            {"diag_code": "C71.0", "name_ko": "뇌, 천막상부의 악성 신생물", "name_en": "Malignant neoplasm of brain, supratentorial", "category": "뇌종양"},
            {"diag_code": "C71.1", "name_ko": "전두엽의 악성 신생물", "name_en": "Malignant neoplasm of frontal lobe", "category": "뇌종양"},
            {"diag_code": "C71.2", "name_ko": "측두엽의 악성 신생물", "name_en": "Malignant neoplasm of temporal lobe", "category": "뇌종양"},
            {"diag_code": "C71.3", "name_ko": "두정엽의 악성 신생물", "name_en": "Malignant neoplasm of parietal lobe", "category": "뇌종양"},
            {"diag_code": "C71.4", "name_ko": "후두엽의 악성 신생물", "name_en": "Malignant neoplasm of occipital lobe", "category": "뇌종양"},
            {"diag_code": "C71.5", "name_ko": "뇌실의 악성 신생물", "name_en": "Malignant neoplasm of cerebral ventricle", "category": "뇌종양"},
            {"diag_code": "C71.6", "name_ko": "소뇌의 악성 신생물", "name_en": "Malignant neoplasm of cerebellum", "category": "뇌종양"},
            {"diag_code": "C71.7", "name_ko": "뇌간의 악성 신생물", "name_en": "Malignant neoplasm of brain stem", "category": "뇌종양"},
            {"diag_code": "D33.0", "name_ko": "뇌, 천막상부의 양성 신생물", "name_en": "Benign neoplasm of brain, supratentorial", "category": "뇌종양"},
            {"diag_code": "D33.1", "name_ko": "뇌, 천막하부의 양성 신생물", "name_en": "Benign neoplasm of brain, infratentorial", "category": "뇌종양"},
            {"diag_code": "D33.2", "name_ko": "뇌의 양성 신생물", "name_en": "Benign neoplasm of brain, unspecified", "category": "뇌종양"},

            # 신경계 퇴행성 질환
            {"diag_code": "G20", "name_ko": "파킨슨병", "name_en": "Parkinson disease", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.0", "name_ko": "알츠하이머병", "name_en": "Alzheimer disease", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.1", "name_ko": "조발성 알츠하이머병", "name_en": "Alzheimer disease with early onset", "category": "퇴행성뇌질환"},
            {"diag_code": "G30.9", "name_ko": "상세불명의 알츠하이머병", "name_en": "Alzheimer disease, unspecified", "category": "퇴행성뇌질환"},
            {"diag_code": "G31.0", "name_ko": "국한성 뇌위축", "name_en": "Circumscribed brain atrophy", "category": "퇴행성뇌질환"},
            {"diag_code": "G35", "name_ko": "다발성 경화증", "name_en": "Multiple sclerosis", "category": "탈수초성질환"},

            # 뇌전증
            {"diag_code": "G40.0", "name_ko": "국소발생 관련성 특발성 뇌전증", "name_en": "Localization-related epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.1", "name_ko": "단순부분발작을 동반한 증상성 국소발생 관련성 뇌전증", "name_en": "Localization-related symptomatic epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.3", "name_ko": "전신성 특발성 뇌전증", "name_en": "Generalized idiopathic epilepsy", "category": "뇌전증"},
            {"diag_code": "G40.9", "name_ko": "상세불명의 뇌전증", "name_en": "Epilepsy, unspecified", "category": "뇌전증"},

            # 뇌염/수막염
            {"diag_code": "G03.0", "name_ko": "비화농성 수막염", "name_en": "Nonpyogenic meningitis", "category": "감염성뇌질환"},
            {"diag_code": "G03.9", "name_ko": "상세불명의 수막염", "name_en": "Meningitis, unspecified", "category": "감염성뇌질환"},
            {"diag_code": "G04.0", "name_ko": "급성 파종성 뇌염", "name_en": "Acute disseminated encephalitis", "category": "감염성뇌질환"},
            {"diag_code": "G04.9", "name_ko": "상세불명의 뇌염, 척수염 및 뇌척수염", "name_en": "Encephalitis, unspecified", "category": "감염성뇌질환"},

            # 기타 신경계 질환
            {"diag_code": "G47.0", "name_ko": "잠들기 어려운 장애(불면증)", "name_en": "Insomnia", "category": "기타신경계질환"},
            {"diag_code": "G47.3", "name_ko": "수면무호흡", "name_en": "Sleep apnea", "category": "기타신경계질환"},
            {"diag_code": "G70.0", "name_ko": "중증 근무력증", "name_en": "Myasthenia gravis", "category": "기타신경계질환"},
            {"diag_code": "G24.1", "name_ko": "특발성 가족성 근긴장이상", "name_en": "Idiopathic familial dystonia", "category": "기타신경계질환"},
            {"diag_code": "G50.0", "name_ko": "삼차신경통", "name_en": "Trigeminal neuralgia", "category": "기타신경계질환"},
            {"diag_code": "G51.0", "name_ko": "벨마비(안면신경마비)", "name_en": "Bell's palsy", "category": "기타신경계질환"},
            {"diag_code": "G80.0", "name_ko": "경직성 뇌성마비", "name_en": "Spastic cerebral palsy", "category": "기타신경계질환"},
            {"diag_code": "G12.2", "name_ko": "운동신경세포질환(ALS 등)", "name_en": "Motor neuron disease", "category": "기타신경계질환"},
            {"diag_code": "G60.0", "name_ko": "유전성 운동 및 감각 신경병증", "name_en": "Hereditary motor and sensory neuropathy", "category": "기타신경계질환"},

            # === 호흡계 질환 (J00-J99: 호흡계통의 질환) ===
            # 상기도 감염
            {"diag_code": "J00", "name_ko": "급성 비인두염(감기)", "name_en": "Acute nasopharyngitis (common cold)", "category": "급성상기도감염"},
            {"diag_code": "J01.0", "name_ko": "급성 상악동염", "name_en": "Acute maxillary sinusitis", "category": "급성상기도감염"},
            {"diag_code": "J01.9", "name_ko": "상세불명의 급성 부비동염", "name_en": "Acute sinusitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J02.0", "name_ko": "연쇄구균 인두염", "name_en": "Streptococcal pharyngitis", "category": "급성상기도감염"},
            {"diag_code": "J02.9", "name_ko": "상세불명의 급성 인두염", "name_en": "Acute pharyngitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J03.0", "name_ko": "연쇄구균 편도염", "name_en": "Streptococcal tonsillitis", "category": "급성상기도감염"},
            {"diag_code": "J03.9", "name_ko": "상세불명의 급성 편도염", "name_en": "Acute tonsillitis, unspecified", "category": "급성상기도감염"},
            {"diag_code": "J04.0", "name_ko": "급성 후두염", "name_en": "Acute laryngitis", "category": "급성상기도감염"},
            {"diag_code": "J06.0", "name_ko": "여러 부위 및 상세불명 부위의 급성 상기도감염", "name_en": "Acute upper respiratory infection", "category": "급성상기도감염"},
            {"diag_code": "J06.9", "name_ko": "상세불명의 급성 상기도감염", "name_en": "Acute upper respiratory infection, unspecified", "category": "급성상기도감염"},

            # 인플루엔자
            {"diag_code": "J10.0", "name_ko": "인플루엔자 바이러스가 확인된 인플루엔자, 폐렴", "name_en": "Influenza with pneumonia", "category": "인플루엔자"},
            {"diag_code": "J10.1", "name_ko": "인플루엔자 바이러스가 확인된 인플루엔자", "name_en": "Influenza with other respiratory manifestations", "category": "인플루엔자"},
            {"diag_code": "J11.0", "name_ko": "인플루엔자 바이러스 미확인, 폐렴", "name_en": "Influenza with pneumonia, virus not identified", "category": "인플루엔자"},
            {"diag_code": "J11.1", "name_ko": "인플루엔자 바이러스 미확인", "name_en": "Influenza, virus not identified", "category": "인플루엔자"},

            # 하기도 감염
            {"diag_code": "J12.0", "name_ko": "아데노바이러스 폐렴", "name_en": "Adenoviral pneumonia", "category": "폐렴"},
            {"diag_code": "J12.9", "name_ko": "상세불명의 바이러스 폐렴", "name_en": "Viral pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J13", "name_ko": "폐렴연쇄구균에 의한 폐렴", "name_en": "Pneumonia due to Streptococcus pneumoniae", "category": "폐렴"},
            {"diag_code": "J14", "name_ko": "헤모필루스 인플루엔자균에 의한 폐렴", "name_en": "Pneumonia due to Haemophilus influenzae", "category": "폐렴"},
            {"diag_code": "J15.0", "name_ko": "클렙시엘라 폐렴간균에 의한 폐렴", "name_en": "Pneumonia due to Klebsiella pneumoniae", "category": "폐렴"},
            {"diag_code": "J15.9", "name_ko": "상세불명의 세균성 폐렴", "name_en": "Bacterial pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J18.0", "name_ko": "기관지폐렴", "name_en": "Bronchopneumonia", "category": "폐렴"},
            {"diag_code": "J18.1", "name_ko": "대엽성 폐렴", "name_en": "Lobar pneumonia", "category": "폐렴"},
            {"diag_code": "J18.9", "name_ko": "상세불명의 폐렴", "name_en": "Pneumonia, unspecified", "category": "폐렴"},
            {"diag_code": "J20.0", "name_ko": "마이코플라스마 폐렴균에 의한 급성 기관지염", "name_en": "Acute bronchitis due to Mycoplasma pneumoniae", "category": "기관지염"},
            {"diag_code": "J20.9", "name_ko": "상세불명의 급성 기관지염", "name_en": "Acute bronchitis, unspecified", "category": "기관지염"},
            {"diag_code": "J21.0", "name_ko": "호흡기 세포융합 바이러스에 의한 급성 세기관지염", "name_en": "Acute bronchiolitis due to RSV", "category": "기관지염"},
            {"diag_code": "J21.9", "name_ko": "상세불명의 급성 세기관지염", "name_en": "Acute bronchiolitis, unspecified", "category": "기관지염"},

            # 만성 하기도 질환
            {"diag_code": "J40", "name_ko": "급성 또는 만성으로 명시되지 않은 기관지염", "name_en": "Bronchitis, not specified", "category": "만성하기도질환"},
            {"diag_code": "J41.0", "name_ko": "단순 만성 기관지염", "name_en": "Simple chronic bronchitis", "category": "만성하기도질환"},
            {"diag_code": "J42", "name_ko": "상세불명의 만성 기관지염", "name_en": "Chronic bronchitis, unspecified", "category": "만성하기도질환"},
            {"diag_code": "J43.0", "name_ko": "맥클라우드 증후군", "name_en": "MacLeod syndrome", "category": "만성하기도질환"},
            {"diag_code": "J43.9", "name_ko": "상세불명의 폐기종", "name_en": "Emphysema, unspecified", "category": "만성하기도질환"},
            {"diag_code": "J44.0", "name_ko": "급성 하기도감염이 동반된 만성폐쇄성폐질환", "name_en": "COPD with acute lower respiratory infection", "category": "COPD"},
            {"diag_code": "J44.1", "name_ko": "급성 악화가 동반된 만성폐쇄성폐질환", "name_en": "COPD with acute exacerbation", "category": "COPD"},
            {"diag_code": "J44.9", "name_ko": "상세불명의 만성폐쇄성폐질환", "name_en": "COPD, unspecified", "category": "COPD"},

            # 천식
            {"diag_code": "J45.0", "name_ko": "알레르기가 주로 작용하는 천식", "name_en": "Predominantly allergic asthma", "category": "천식"},
            {"diag_code": "J45.1", "name_ko": "비알레르기성 천식", "name_en": "Nonallergic asthma", "category": "천식"},
            {"diag_code": "J45.8", "name_ko": "혼합형 천식", "name_en": "Mixed asthma", "category": "천식"},
            {"diag_code": "J45.9", "name_ko": "상세불명의 천식", "name_en": "Asthma, unspecified", "category": "천식"},

            # 기타 호흡기 질환
            {"diag_code": "J84.0", "name_ko": "폐포성 및 폐포벽 병태", "name_en": "Alveolar and parietoalveolar conditions", "category": "간질성폐질환"},
            {"diag_code": "J84.1", "name_ko": "기타 간질성 폐질환", "name_en": "Other interstitial pulmonary diseases", "category": "간질성폐질환"},
            {"diag_code": "J90", "name_ko": "달리 분류되지 않은 흉수", "name_en": "Pleural effusion", "category": "흉막질환"},
            {"diag_code": "J93.0", "name_ko": "자연기흉", "name_en": "Spontaneous tension pneumothorax", "category": "흉막질환"},
            {"diag_code": "J93.1", "name_ko": "기타 자연기흉", "name_en": "Other spontaneous pneumothorax", "category": "흉막질환"},
            {"diag_code": "J96.0", "name_ko": "급성 호흡부전", "name_en": "Acute respiratory failure", "category": "호흡부전"},
            {"diag_code": "J96.1", "name_ko": "만성 호흡부전", "name_en": "Chronic respiratory failure", "category": "호흡부전"},
            {"diag_code": "J96.9", "name_ko": "상세불명의 호흡부전", "name_en": "Respiratory failure, unspecified", "category": "호흡부전"},

            # 추가 호흡기 및 상기도 질환
            {"diag_code": "J30.1", "name_ko": "꽃가루에 의한 알레르기비염", "name_en": "Allergic rhinitis due to pollen", "category": "기타호흡기질환"},
            {"diag_code": "J32.0", "name_ko": "만성 상악동염", "name_en": "Chronic maxillary sinusitis", "category": "기타호흡기질환"},
            {"diag_code": "J34.2", "name_ko": "코중격 만곡", "name_en": "Deviated nasal septum", "category": "기타호흡기질환"},
            {"diag_code": "J35.0", "name_ko": "만성 편도염", "name_en": "Chronic tonsillitis", "category": "기타호흡기질환"},
            {"diag_code": "J81", "name_ko": "폐부종", "name_en": "Pulmonary edema", "category": "기타호흡기질환"},
            {"diag_code": "J80", "name_ko": "성인호흡곤란증후군(ARDS)", "name_en": "Adult respiratory distress syndrome", "category": "기타호흡기질환"},
            {"diag_code": "J82", "name_ko": "달리 분류되지 않은 폐호산구증가증", "name_en": "Pulmonary eosinophilia", "category": "기타호흡기질환"},
            {"diag_code": "J60", "name_ko": "탄광부진폐증", "name_en": "Coalworker's pneumoconiosis", "category": "진폐증"},
            {"diag_code": "J67.0", "name_ko": "농부폐", "name_en": "Farmer's lung", "category": "기타호흡기질환"},
            {"diag_code": "J98.1", "name_ko": "폐허탈(무기폐)", "name_en": "Pulmonary collapse", "category": "기타호흡기질환"},
        ]

    def _print_final_stats(self, stats):
        """최종 통계 출력"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("[STATISTICS] Seeding Statistics"))
        self.stdout.write("=" * 80)

        total_created = 0
        total_updated = 0
        total_errors = 0

        for data_type, stat in stats.items():
            if stat['created'] > 0 or stat['updated'] > 0 or stat['errors'] > 0:
                self.stdout.write(f"\n{data_type.upper()}:")
                self.stdout.write(f"  [+] Created: {stat['created']}")
                self.stdout.write(f"  [~] Updated: {stat['updated']}")
                self.stdout.write(f"  [!] Errors: {stat['errors']}")
                self.stdout.write(f"  [=] Total: {stat['created'] + stat['updated']}")

                total_created += stat['created']
                total_updated += stat['updated']
                total_errors += stat['errors']

        self.stdout.write("\n" + "-" * 80)
        self.stdout.write(self.style.SUCCESS(f"SUMMARY:"))
        self.stdout.write(f"  [+] Total Created: {total_created}")
        self.stdout.write(f"  [~] Total Updated: {total_updated}")
        self.stdout.write(f"  [!] Total Errors: {total_errors}")
        self.stdout.write(f"  [=] Total Records: {total_created + total_updated}")

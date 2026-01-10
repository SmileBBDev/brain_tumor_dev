#!/usr/bin/env python
"""
Brain Tumor CDSS - 더미 데이터 설정 스크립트 (2/2) - 추가 데이터

이 스크립트는 추가 더미 데이터를 생성합니다:
- 치료 계획 데이터
- 경과 추적 데이터
- AI 추론 요청 데이터

사용법:
    python setup_dummy_data_2_add.py          # 기존 데이터 유지, 부족분만 추가
    python setup_dummy_data_2_add.py --reset  # 추가 데이터만 삭제 후 새로 생성
    python setup_dummy_data_2_add.py --force  # 목표 수량 이상이어도 강제 추가

선행 조건:
    python setup_database.py        (마이그레이션 및 기본 데이터)
    python setup_dummy_data_1_base.py  (기본 더미 데이터)
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
import random
import argparse

# 프로젝트 루트 디렉토리로 이동 (상위 폴더)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Django 설정 (sys.path에 프로젝트 루트 추가)
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 초기화
import django
django.setup()

from django.utils import timezone
from django.db import transaction


def check_prerequisites():
    """선행 조건 확인"""
    print("\n[0단계] 선행 조건 확인...")

    from django.contrib.auth import get_user_model
    from apps.patients.models import Patient
    from apps.ai_inference.models import AIModel

    User = get_user_model()

    # 사용자 확인
    if not User.objects.exists():
        print("[ERROR] 사용자가 없습니다.")
        print("  먼저 실행하세요: python setup_database.py")
        return False

    # 환자 확인
    if not Patient.objects.filter(is_deleted=False).exists():
        print("[ERROR] 환자가 없습니다.")
        print("  먼저 실행하세요: python setup_dummy_data_1_base.py")
        return False

    # AI 모델 확인
    if not AIModel.objects.filter(is_active=True).exists():
        print("[WARNING] AI 모델이 없습니다. AI 요청 생성이 제한될 수 있습니다.")

    print("[OK] 선행 조건 충족")
    return True


def create_dummy_treatment_plans(num_plans=15, force=False):
    """더미 치료 계획 데이터 생성"""
    print(f"\n[1단계] 치료 계획 데이터 생성 (목표: {num_plans}건)...")

    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = TreatmentPlan.objects.count()
    if existing_count >= num_plans and not force:
        print(f"[SKIP] 이미 {existing_count}건의 치료 계획이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    # 실제 모델의 choices 사용
    treatment_types = [choice[0] for choice in TreatmentPlan.TreatmentType.choices]
    treatment_goals = [choice[0] for choice in TreatmentPlan.TreatmentGoal.choices]
    statuses = [choice[0] for choice in TreatmentPlan.Status.choices]

    plan_summaries = {
        'surgery': ['뇌종양 절제술 시행 예정', '내시경 수술 계획', '감압술 시행', '조직 검사 후 치료 방향 결정'],
        'radiation': ['전뇌 방사선 치료 진행', '정위적 방사선 수술 계획', 'IMRT 치료 시행', '양성자 치료 고려'],
        'chemotherapy': ['테모졸로마이드 치료 시작', '베바시주맙 치료 진행', '복합 항암 요법 적용', '면역 항암 치료 시행'],
        'observation': ['정기 MRI 추적 관찰', '증상 모니터링 지속', '경과 관찰 후 치료 결정'],
        'combined': ['수술 후 방사선+항암 병합', '동시 화학방사선 요법 진행', '복합 치료 프로토콜 적용']
    }

    created_count = 0

    for i in range(num_plans):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        treatment_type = random.choice(treatment_types)
        treatment_goal = random.choice(treatment_goals)
        status = random.choice(statuses)

        days_ago = random.randint(0, 180)
        start_date = timezone.now().date() - timedelta(days=days_ago)

        end_date = None
        actual_start = None
        actual_end = None

        if status == 'completed':
            actual_start = start_date
            actual_end = start_date + timedelta(days=random.randint(14, 90))
            end_date = actual_end
        elif status == 'in_progress':
            actual_start = start_date
            end_date = start_date + timedelta(days=random.randint(30, 120))
        elif status == 'cancelled':
            end_date = start_date + timedelta(days=random.randint(7, 30))
        elif status == 'planned':
            end_date = start_date + timedelta(days=random.randint(30, 90))

        try:
            with transaction.atomic():
                plan = TreatmentPlan.objects.create(
                    patient=patient,
                    treatment_type=treatment_type,
                    treatment_goal=treatment_goal,
                    plan_summary=random.choice(plan_summaries[treatment_type]),
                    planned_by=doctor,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    actual_start_date=actual_start,
                    actual_end_date=actual_end,
                    notes=f"담당의: {doctor.name}" if random.random() < 0.3 else ""
                )

                # 치료 세션 생성 (방사선, 항암의 경우)
                if treatment_type in ['radiation', 'chemotherapy'] and status in ['in_progress', 'completed']:
                    num_sessions = random.randint(3, 8)
                    session_statuses = [choice[0] for choice in TreatmentSession.Status.choices]

                    for j in range(num_sessions):
                        session_datetime = timezone.now() - timedelta(days=days_ago - j * 7)
                        if session_datetime < timezone.now():
                            session_status = 'completed'
                        else:
                            session_status = 'scheduled'

                        TreatmentSession.objects.create(
                            treatment_plan=plan,
                            session_number=j + 1,
                            session_date=session_datetime,
                            performed_by=doctor if session_status == 'completed' else None,
                            status=session_status,
                            session_note=f"{j + 1}회차 치료 진행" if session_status == 'completed' else ""
                        )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 치료 계획 생성: {created_count}건")
    print(f"  현재 전체 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  현재 전체 치료 세션: {TreatmentSession.objects.count()}건")
    return True


def create_dummy_followups(num_followups=25, force=False):
    """더미 경과 추적 데이터 생성"""
    print(f"\n[2단계] 경과 추적 데이터 생성 (목표: {num_followups}건)...")

    from apps.followup.models import FollowUp
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = FollowUp.objects.count()
    if existing_count >= num_followups and not force:
        print(f"[SKIP] 이미 {existing_count}건의 경과 기록이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    # 실제 모델의 choices 사용
    followup_types = [choice[0] for choice in FollowUp.FollowUpType.choices]
    clinical_statuses = [choice[0] for choice in FollowUp.ClinicalStatus.choices]

    symptoms_list = [
        ['두통'], ['어지러움'], ['시야 흐림'], ['손발 저림'],
        [], ['피로감'], ['기억력 저하'], ['수면 장애'],
        ['오심', '구토'], ['경련']
    ]

    notes_list = [
        '전반적으로 안정적인 상태 유지',
        '영상 소견상 변화 없음',
        '치료 반응 양호',
        '경미한 증상 악화 관찰',
        '추가 검사 필요',
        '현 치료 계획 유지 권고',
        '다음 정기 검진 예정',
        'MRI 추적 검사 예정'
    ]

    created_count = 0

    for i in range(num_followups):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        followup_type = random.choice(followup_types)
        clinical_status = random.choice(clinical_statuses)

        days_ago = random.randint(0, 365)
        followup_datetime = timezone.now() - timedelta(days=days_ago)

        # 다음 방문일 (50% 확률로 설정)
        next_followup = None
        if random.random() < 0.5:
            next_followup = followup_datetime.date() + timedelta(days=random.randint(30, 90))

        # 바이탈 사인 (JSON 형식)
        vitals = {}
        if random.random() < 0.6:
            vitals = {
                'bp_systolic': random.randint(110, 140),
                'bp_diastolic': random.randint(70, 90),
                'heart_rate': random.randint(60, 100),
                'temperature': round(random.uniform(36.0, 37.5), 1)
            }

        try:
            FollowUp.objects.create(
                patient=patient,
                followup_date=followup_datetime,
                followup_type=followup_type,
                clinical_status=clinical_status,
                symptoms=random.choice(symptoms_list) if random.random() < 0.7 else [],
                kps_score=random.choice([None, 70, 80, 90, 100]),
                ecog_score=random.choice([None, 0, 1, 2]),
                vitals=vitals,
                weight_kg=round(random.uniform(50, 85), 2) if random.random() < 0.6 else None,
                note=random.choice(notes_list),
                next_followup_date=next_followup,
                recorded_by=doctor
            )
            created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] 경과 기록 생성: {created_count}건")
    print(f"  현재 전체 경과 기록: {FollowUp.objects.count()}건")
    return True


def create_dummy_ai_requests(num_requests=10, force=False):
    """더미 AI 추론 요청 데이터 생성"""
    print(f"\n[3단계] AI 추론 요청 데이터 생성 (목표: {num_requests}건)...")

    from apps.ai_inference.models import AIModel, AIInferenceRequest, AIInferenceResult
    from apps.patients.models import Patient
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # 기존 데이터 확인
    existing_count = AIInferenceRequest.objects.count()
    if existing_count >= num_requests and not force:
        print(f"[SKIP] 이미 {existing_count}건의 AI 요청이 존재합니다.")
        return True

    # 필요한 데이터
    patients = list(Patient.objects.filter(is_deleted=False))
    doctors = list(User.objects.filter(role__code='DOCTOR'))
    ai_models = list(AIModel.objects.filter(is_active=True))

    if not patients:
        print("[ERROR] 환자가 없습니다.")
        return False

    if not doctors:
        doctors = list(User.objects.all()[:1])

    if not ai_models:
        print("[ERROR] 활성화된 AI 모델이 없습니다.")
        print("  먼저 실행하세요: python setup_dummy_data_1_base.py")
        return False

    # AIInferenceRequest.Status에 맞춤
    statuses = ['PENDING', 'VALIDATING', 'PROCESSING', 'COMPLETED', 'FAILED']
    priorities = ['low', 'normal', 'high', 'urgent']

    created_count = 0

    for i in range(num_requests):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        model = random.choice(ai_models)
        status = random.choice(statuses)

        days_ago = random.randint(0, 60)
        requested_at = timezone.now() - timedelta(days=days_ago)

        # 시작/완료 시간 설정
        started_at = None
        completed_at = None
        error_message = None

        if status in ['PROCESSING', 'COMPLETED', 'FAILED']:
            started_at = requested_at + timedelta(minutes=random.randint(1, 30))

        if status == 'COMPLETED':
            completed_at = started_at + timedelta(minutes=random.randint(5, 60)) if started_at else None
        elif status == 'FAILED':
            completed_at = started_at + timedelta(minutes=random.randint(1, 10)) if started_at else None
            error_message = random.choice([
                "입력 데이터 검증 실패",
                "모델 처리 중 오류 발생",
                "타임아웃 초과",
                "필수 데이터 누락"
            ])

        try:
            with transaction.atomic():
                ai_request = AIInferenceRequest.objects.create(
                    patient=patient,
                    model=model,
                    requested_by=doctor,
                    status=status,
                    priority=random.choice(priorities),
                    ocs_references=[],
                    input_data={"patient_id": patient.id, "model_code": model.code},
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message=error_message,
                )

                # COMPLETED인 경우 결과도 생성
                if status == 'COMPLETED':
                    tumor_detected = random.random() < 0.7
                    result_data = {
                        "analysis_type": model.code,
                        "tumor_detected": tumor_detected,
                        "tumor_grade": random.choice(['Grade I', 'Grade II', 'Grade III', 'Grade IV']) if tumor_detected else None,
                        "tumor_location": random.choice(["frontal", "temporal", "parietal", "occipital"]) if tumor_detected else None,
                        "recommendations": [
                            "추가 영상 검사 권장" if tumor_detected else "정기 검진 권장",
                            "전문의 상담 권장"
                        ],
                    }

                    review_status = random.choice(['pending', 'approved', 'rejected'])
                    reviewed_by = doctor if review_status != 'pending' else None
                    reviewed_at = completed_at + timedelta(hours=random.randint(1, 48)) if reviewed_by else None

                    AIInferenceResult.objects.create(
                        inference_request=ai_request,
                        result_data=result_data,
                        confidence_score=round(random.uniform(0.75, 0.98), 2),
                        visualization_paths=[],
                        reviewed_by=reviewed_by,
                        review_status=review_status,
                        review_comment="결과 확인함" if reviewed_by else None,
                        reviewed_at=reviewed_at,
                    )

                created_count += 1

        except Exception as e:
            print(f"  오류: {e}")

    print(f"[OK] AI 요청 생성: {created_count}건")
    print(f"  현재 전체 AI 요청: {AIInferenceRequest.objects.count()}건")
    return True


def reset_add_data():
    """추가 더미 데이터만 삭제 (base 데이터는 유지)"""
    print("\n[RESET] 추가 더미 데이터 삭제 중...")

    from apps.ai_inference.models import AIInferenceRequest, AIInferenceResult, AIInferenceLog
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp

    # 삭제 순서: 의존성 역순
    # AI 로그/결과/요청 삭제
    ai_log_count = AIInferenceLog.objects.count()
    AIInferenceLog.objects.all().delete()
    print(f"  AIInferenceLog: {ai_log_count}건 삭제")

    ai_result_count = AIInferenceResult.objects.count()
    AIInferenceResult.objects.all().delete()
    print(f"  AIInferenceResult: {ai_result_count}건 삭제")

    ai_request_count = AIInferenceRequest.objects.count()
    AIInferenceRequest.objects.all().delete()
    print(f"  AIInferenceRequest: {ai_request_count}건 삭제")

    # 치료 세션/계획 삭제
    treatment_session_count = TreatmentSession.objects.count()
    TreatmentSession.objects.all().delete()
    print(f"  TreatmentSession: {treatment_session_count}건 삭제")

    treatment_plan_count = TreatmentPlan.objects.count()
    TreatmentPlan.objects.all().delete()
    print(f"  TreatmentPlan: {treatment_plan_count}건 삭제")

    # 경과 기록 삭제
    followup_count = FollowUp.objects.count()
    FollowUp.objects.all().delete()
    print(f"  FollowUp: {followup_count}건 삭제")

    print("[OK] 추가 더미 데이터 삭제 완료")


def print_summary():
    """추가 더미 데이터 요약"""
    print("\n" + "="*60)
    print("추가 더미 데이터 생성 완료!")
    print("="*60)

    from apps.ai_inference.models import AIModel, AIInferenceRequest
    from apps.treatment.models import TreatmentPlan, TreatmentSession
    from apps.followup.models import FollowUp

    print(f"\n[통계 - 추가 데이터]")
    print(f"  - 치료 계획: {TreatmentPlan.objects.count()}건")
    print(f"  - 치료 세션: {TreatmentSession.objects.count()}건")
    print(f"  - 경과 기록: {FollowUp.objects.count()}건")
    print(f"  - AI 모델: {AIModel.objects.count()}개")
    print(f"  - AI 요청: {AIInferenceRequest.objects.count()}건")

    print(f"\n[다음 단계]")
    print(f"  서버 실행:")
    print(f"    python manage.py runserver")
    print(f"")
    print(f"  테스트 계정:")
    print(f"    system / system001 (시스템 관리자)")
    print(f"    admin / admin001 (병원 관리자)")
    print(f"    doctor1~5 / doctor001~005 (의사 5명)")
    print(f"    nurse1 / nurse001 (간호사)")
    print(f"    ris1 / ris001 (영상과)")
    print(f"    lis1 / lis001 (검사과)")


def main():
    """메인 실행 함수"""
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='Brain Tumor CDSS 추가 더미 데이터 생성')
    parser.add_argument('--reset', action='store_true', help='추가 데이터만 삭제 후 새로 생성')
    parser.add_argument('--force', action='store_true', help='목표 수량 이상이어도 강제 추가')
    args = parser.parse_args()

    print("="*60)
    print("Brain Tumor CDSS - 추가 더미 데이터 생성 (2/2)")
    print("="*60)

    # 선행 조건 확인
    if not check_prerequisites():
        sys.exit(1)

    # --reset 옵션: 추가 데이터만 삭제
    if args.reset:
        confirm = input("\n추가 데이터(치료계획, 경과추적, AI요청)를 삭제하시겠습니까? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_add_data()
        else:
            print("삭제 취소됨")
            sys.exit(0)

    force = args.reset or args.force  # reset 시에는 force=True

    # 치료 계획 데이터 생성
    create_dummy_treatment_plans(15, force=force)

    # 경과 추적 데이터 생성
    create_dummy_followups(25, force=force)

    # AI 요청 데이터 생성
    create_dummy_ai_requests(10, force=force)

    # 요약 출력
    print_summary()


if __name__ == '__main__':
    main()

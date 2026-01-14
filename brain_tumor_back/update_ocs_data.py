#!/usr/bin/env python
"""
AI 모델 및 OCS 데이터 업데이트 스크립트

실행 방법:
    python update_ocs_data.py

업데이트 내용:
1. AI 모델의 required_keys를 job_type 기반으로 변경
2. LIS OCS의 job_type을 표준화 (RNA_SEQ, BIOMARKER 등)
"""

import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.ocs.models import OCS
from apps.ai_inference.models import AIModel


def update_ai_models():
    """AI 모델의 required_keys를 job_type 기반으로 업데이트"""
    print("\n[1단계] AI 모델 required_keys 업데이트...")

    updates = {
        'M1': {
            'name': 'MRI 4-Channel Analysis',
            'description': 'MRI 4채널(T1, T2, T1C, FLAIR) 기반 뇌종양 분석 모델',
            'ocs_sources': ['RIS'],
            'required_keys': {'RIS': ['MRI']}
        },
        'MG': {
            'name': 'Genetic Analysis',
            'description': 'RNA 시퀀싱 기반 유전자 분석 모델 (MGMT 메틸화, IDH 변이 등)',
            'ocs_sources': ['LIS'],
            'required_keys': {'LIS': ['RNA_SEQ']}
        },
        'MM': {
            'name': 'Multimodal Analysis',
            'description': 'MRI + RNA시퀀싱 + 바이오마커 통합 분석 모델 (종합 예후 예측)',
            'ocs_sources': ['RIS', 'LIS'],
            'required_keys': {
                'RIS': ['MRI'],
                'LIS': ['RNA_SEQ', 'BIOMARKER']
            }
        }
    }

    updated_count = 0
    for code, data in updates.items():
        try:
            model = AIModel.objects.get(code=code)
            model.name = data['name']
            model.description = data['description']
            model.ocs_sources = data['ocs_sources']
            model.required_keys = data['required_keys']
            model.save()
            updated_count += 1
            print(f"  - {code}: required_keys 업데이트 완료 → {data['required_keys']}")
        except AIModel.DoesNotExist:
            print(f"  - {code}: 모델이 존재하지 않음, 생성 중...")
            AIModel.objects.create(
                code=code,
                name=data['name'],
                description=data['description'],
                ocs_sources=data['ocs_sources'],
                required_keys=data['required_keys'],
                is_active=True
            )
            updated_count += 1
            print(f"  - {code}: 모델 생성 완료")

    print(f"[OK] AI 모델 업데이트 완료: {updated_count}건")
    return updated_count


def normalize_lis_job_types():
    """LIS OCS의 job_type을 표준화"""
    print("\n[2단계] LIS OCS job_type 표준화...")

    # job_type 매핑 (기존 → 표준)
    job_type_mapping = {
        # 유전자 검사 → RNA_SEQ
        'GENETIC': 'RNA_SEQ',
        'DNA_SEQ': 'RNA_SEQ',
        'GENE_PANEL': 'RNA_SEQ',
        # 단백질 검사 → BIOMARKER
        'PROTEIN': 'BIOMARKER',
        'PROTEIN_PANEL': 'BIOMARKER',
    }

    updated_count = 0
    for old_type, new_type in job_type_mapping.items():
        ocs_list = OCS.objects.filter(
            job_role='LIS',
            job_type=old_type
        )
        count = ocs_list.count()
        if count > 0:
            ocs_list.update(job_type=new_type)
            updated_count += count
            print(f"  - {old_type} → {new_type}: {count}건 변경")

    print(f"[OK] LIS OCS job_type 표준화 완료: {updated_count}건")
    return updated_count


def show_ocs_summary():
    """OCS 현황 요약"""
    print("\n" + "=" * 60)
    print("OCS 현황 요약")
    print("=" * 60)

    # RIS
    print("\n[RIS 영상검사]")
    ris_types = OCS.objects.filter(job_role='RIS').values_list('job_type', flat=True).distinct()
    for job_type in ris_types:
        count = OCS.objects.filter(job_role='RIS', job_type=job_type, ocs_status='CONFIRMED').count()
        total = OCS.objects.filter(job_role='RIS', job_type=job_type).count()
        print(f"  - {job_type}: {count}건 (CONFIRMED) / {total}건 (전체)")

    # LIS
    print("\n[LIS 검사실]")
    lis_types = OCS.objects.filter(job_role='LIS').values_list('job_type', flat=True).distinct()
    for job_type in lis_types:
        count = OCS.objects.filter(job_role='LIS', job_type=job_type, ocs_status='CONFIRMED').count()
        total = OCS.objects.filter(job_role='LIS', job_type=job_type).count()
        print(f"  - {job_type}: {count}건 (CONFIRMED) / {total}건 (전체)")

    # AI 모델
    print("\n[AI 모델 요구사항]")
    for model in AIModel.objects.filter(is_active=True):
        print(f"  - {model.code} ({model.name}): {model.required_keys}")


def main():
    print("=" * 60)
    print("AI 모델 및 OCS 데이터 업데이트 스크립트")
    print("=" * 60)

    # 현재 상태 출력
    total_ocs = OCS.objects.count()
    ris_ocs = OCS.objects.filter(job_role='RIS').count()
    lis_ocs = OCS.objects.filter(job_role='LIS').count()

    print(f"\n현재 OCS 현황:")
    print(f"  - 전체 OCS: {total_ocs}건")
    print(f"  - RIS OCS: {ris_ocs}건")
    print(f"  - LIS OCS: {lis_ocs}건")

    # 업데이트 실행
    ai_updated = update_ai_models()
    lis_updated = normalize_lis_job_types()

    # 최종 현황 출력
    show_ocs_summary()

    print("\n" + "=" * 60)
    print("업데이트 완료 요약:")
    print(f"  - AI 모델 required_keys 업데이트: {ai_updated}건")
    print(f"  - LIS OCS job_type 표준화: {lis_updated}건")
    print("=" * 60)


if __name__ == '__main__':
    main()

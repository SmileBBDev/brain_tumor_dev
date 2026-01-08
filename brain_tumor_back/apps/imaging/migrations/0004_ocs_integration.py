# Generated manually for OCS integration
# 기존 ImagingStudy/ImagingReport 데이터를 OCS로 마이그레이션

import django.db.models.deletion
from django.db import migrations, models


def migrate_data_to_ocs(apps, schema_editor):
    """
    기존 ImagingStudy 데이터를 OCS로 마이그레이션
    """
    OCS = apps.get_model('ocs', 'OCS')
    ImagingStudy = apps.get_model('imaging', 'ImagingStudy')
    ImagingReport = apps.get_model('imaging', 'ImagingReport')

    for study in ImagingStudy.objects.all():
        # OCS 상태 매핑
        status_map = {
            'ordered': 'ORDERED',
            'scheduled': 'ACCEPTED',
            'in-progress': 'IN_PROGRESS',
            'completed': 'RESULT_READY',
            'reported': 'CONFIRMED',
            'cancelled': 'CANCELLED',
        }
        ocs_status = status_map.get(study.status, 'ORDERED')

        # doctor_request 구성
        doctor_request = {
            "_template": "RIS",
            "_version": "1.0",
            "clinical_info": study.clinical_info or "",
            "special_instruction": study.special_instruction or "",
            "body_part": study.body_part or "brain",
            "_custom": {}
        }

        # worker_result 구성
        worker_result = {
            "_template": "RIS",
            "_version": "1.0",
            "_confirmed": False,
            "dicom": {
                "study_uid": study.study_uid or "",
                "series": [],
                "accession_number": "",
                "series_count": study.series_count or 0,
                "instance_count": study.instance_count or 0
            },
            "impression": "",
            "findings": "",
            "recommendation": "",
            "tumor": {
                "detected": False,
                "location": {"lobe": "", "hemisphere": ""},
                "size": {"max_diameter_cm": None, "volume_cc": None}
            },
            "work_notes": [],
            "_custom": {}
        }

        # ImagingReport가 있으면 worker_result에 반영
        try:
            report = ImagingReport.objects.get(imaging_study=study)
            worker_result["findings"] = report.findings or ""
            worker_result["impression"] = report.impression or ""
            worker_result["_confirmed"] = (report.status == 'signed')

            if report.tumor_detected:
                worker_result["tumor"]["detected"] = True
                if report.tumor_location:
                    worker_result["tumor"]["location"] = report.tumor_location
                if report.tumor_size:
                    worker_result["tumor"]["size"] = report.tumor_size
        except ImagingReport.DoesNotExist:
            pass

        # work_note가 있으면 work_notes에 추가
        if hasattr(study, 'work_note') and study.work_note:
            worker_result["work_notes"].append({
                "timestamp": study.created_at.isoformat() if study.created_at else "",
                "author": "System Migration",
                "content": study.work_note
            })

        # OCS 생성
        ocs = OCS.objects.create(
            patient=study.patient,
            doctor=study.ordered_by,
            worker=study.radiologist,
            encounter=study.encounter,
            job_role='RIS',
            job_type=study.modality,
            ocs_status=ocs_status,
            doctor_request=doctor_request,
            worker_result=worker_result,
            priority='normal',
            is_deleted=study.is_deleted,
        )

        # 타임스탬프 설정
        if ocs_status == 'ACCEPTED':
            ocs.accepted_at = study.scheduled_at or study.created_at
        elif ocs_status == 'IN_PROGRESS':
            ocs.accepted_at = study.scheduled_at or study.created_at
            ocs.in_progress_at = study.performed_at or study.created_at
        elif ocs_status == 'RESULT_READY':
            ocs.accepted_at = study.scheduled_at or study.created_at
            ocs.in_progress_at = study.performed_at or study.created_at
            ocs.result_ready_at = study.updated_at
        elif ocs_status == 'CONFIRMED':
            ocs.accepted_at = study.scheduled_at or study.created_at
            ocs.in_progress_at = study.performed_at or study.created_at
            ocs.result_ready_at = study.updated_at
            ocs.confirmed_at = study.updated_at
        elif ocs_status == 'CANCELLED':
            ocs.cancelled_at = study.updated_at

        ocs.save()

        # ImagingStudy에 임시로 ocs_id 저장 (나중에 FK 연결용)
        study._temp_ocs_id = ocs.id
        study.save()


def reverse_migration(apps, schema_editor):
    """역방향 마이그레이션 - OCS에서 다시 분리"""
    # 복잡한 역마이그레이션은 지원하지 않음
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("imaging", "0003_add_work_note"),
        ("ocs", "0001_initial"),
    ]

    operations = [
        # 1. 먼저 데이터 마이그레이션 실행 (기존 구조 유지한 채)
        migrations.RunPython(migrate_data_to_ocs, reverse_migration),

        # 2. ImagingReport 테이블 삭제
        migrations.DeleteModel(name="ImagingReport"),

        # 3. 기존 인덱스 제거
        migrations.RemoveIndex(
            model_name="imagingstudy",
            name="imaging_stu_patient_b9b5ca_idx",
        ),
        migrations.RemoveIndex(
            model_name="imagingstudy",
            name="imaging_stu_encount_e4430c_idx",
        ),
        migrations.RemoveIndex(
            model_name="imagingstudy",
            name="imaging_stu_status_70677c_idx",
        ),

        # 4. 기존 필드 제거
        migrations.RemoveField(model_name="imagingstudy", name="patient"),
        migrations.RemoveField(model_name="imagingstudy", name="encounter"),
        migrations.RemoveField(model_name="imagingstudy", name="ordered_by"),
        migrations.RemoveField(model_name="imagingstudy", name="radiologist"),
        migrations.RemoveField(model_name="imagingstudy", name="status"),
        migrations.RemoveField(model_name="imagingstudy", name="ordered_at"),
        migrations.RemoveField(model_name="imagingstudy", name="clinical_info"),
        migrations.RemoveField(model_name="imagingstudy", name="special_instruction"),
        migrations.RemoveField(model_name="imagingstudy", name="work_note"),

        # 5. OCS FK 추가
        migrations.AddField(
            model_name="imagingstudy",
            name="ocs",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="imaging_study",
                to="ocs.ocs",
                verbose_name="OCS 오더",
                help_text="연결된 OCS 오더 (job_role=RIS)",
                null=True,  # 임시로 null 허용 (데이터 연결 후 변경)
            ),
        ),

        # 6. accession_number 추가
        migrations.AddField(
            model_name="imagingstudy",
            name="accession_number",
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                verbose_name="Accession Number",
            ),
        ),

        # 7. 새 인덱스 추가
        migrations.AddIndex(
            model_name="imagingstudy",
            index=models.Index(fields=["ocs"], name="imaging_stu_ocs_id_idx"),
        ),
        migrations.AddIndex(
            model_name="imagingstudy",
            index=models.Index(fields=["study_uid"], name="imaging_stu_study_uid_idx"),
        ),

        # 8. Meta 옵션 변경
        migrations.AlterModelOptions(
            name="imagingstudy",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "영상 검사 (DICOM)",
                "verbose_name_plural": "영상 검사 목록 (DICOM)",
            },
        ),
    ]

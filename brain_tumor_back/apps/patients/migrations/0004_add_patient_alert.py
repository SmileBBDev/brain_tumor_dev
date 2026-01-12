# Generated manually for PatientAlert model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("patients", "0003_add_chief_complaint"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientAlert",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("ALLERGY", "알레르기"),
                            ("CONTRAINDICATION", "금기사항"),
                            ("PRECAUTION", "주의사항"),
                            ("OTHER", "기타"),
                        ],
                        max_length=20,
                        verbose_name="주의사항 유형",
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("HIGH", "높음"),
                            ("MEDIUM", "중간"),
                            ("LOW", "낮음"),
                        ],
                        default="MEDIUM",
                        max_length=10,
                        verbose_name="심각도",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=200, verbose_name="제목"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="상세 설명"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="활성 여부"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="생성일시"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="수정일시"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_alerts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="등록자",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="patients.patient",
                        verbose_name="환자",
                    ),
                ),
            ],
            options={
                "verbose_name": "환자 주의사항",
                "verbose_name_plural": "환자 주의사항 목록",
                "db_table": "patient_alerts",
                "ordering": ["-severity", "-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="patientalert",
            index=models.Index(
                fields=["patient", "alert_type"], name="patient_ale_patient_7f1a3e_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="patientalert",
            index=models.Index(
                fields=["patient", "is_active"], name="patient_ale_patient_6c4b2f_idx"
            ),
        ),
    ]

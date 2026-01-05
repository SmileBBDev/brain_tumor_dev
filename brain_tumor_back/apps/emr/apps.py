from django.apps import AppConfig


class EmrConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.emr"

    # def ready(self):
    #     """앱 시작 시 OpenEMR 자동 동기화 signals 활성화"""
    #     # PatientCache → OpenEMR Patient 자동 동기화
    #     import emr.signals  # noqa

from django.apps import AppConfig


class FhirConfig(AppConfig):
    name = "apps.fhir"

    # def ready(self):
    #     """앱 시작 시 FHIR 자동 동기화 signals 활성화"""
    #     # PatientCache → FHIR Patient 자동 동기화
    #     import fhir.signals  # noqa

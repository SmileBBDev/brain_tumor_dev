"""
FHIR Converters

Django 모델을 HL7 FHIR R4 표준 리소스로 변환하는 컨버터 모듈
"""
from typing import Dict, Optional
from datetime import datetime
from django.conf import settings


class FHIRConverter:
    """FHIR R4 표준 변환기 Base Class"""

    FHIR_VERSION = "4.0.1"

    @staticmethod
    def get_meta(resource_type: str, last_updated: datetime = None) -> Dict:
        """FHIR Meta 요소 생성"""
        meta = {
            "versionId": "1",
            "lastUpdated": (last_updated or datetime.now()).isoformat()
        }
        return meta

    @staticmethod
    def get_identifier(system: str, value: str) -> Dict:
        """FHIR Identifier 요소 생성"""
        return {
            "system": system,
            "value": value
        }


class PatientConverter(FHIRConverter):
    """Patient 리소스 컨버터"""

    @staticmethod
    def to_fhir(patient) -> Dict:
        """
        Django Patient 모델 → FHIR Patient Resource

        Args:
            patient: emr.models.PatientCache 인스턴스

        Returns:
            FHIR Patient Resource (dict)
        """
        resource = {
            "resourceType": "Patient",
            "id": patient.patient_id,
            "meta": FHIRConverter.get_meta("Patient", patient.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/patient",
                    patient.patient_id
                )
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": patient.last_name or "",
                    "given": [patient.first_name or ""],
                    "text": f"{patient.last_name or ''} {patient.first_name or ''}".strip()
                }
            ],
            "gender": PatientConverter._map_gender(patient.gender),
            "birthDate": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
        }

        # Telecom (전화번호, 이메일)
        telecom = []
        if patient.phone:
            telecom.append({
                "system": "phone",
                "value": patient.phone,
                "use": "mobile"
            })
        if patient.email:
            telecom.append({
                "system": "email",
                "value": patient.email,
                "use": "home"
            })
        if telecom:
            resource["telecom"] = telecom

        # Address
        if patient.address:
            resource["address"] = [{
                "use": "home",
                "type": "physical",
                "text": patient.address
            }]

        return resource

    @staticmethod
    def _map_gender(gender: str) -> str:
        """성별 코드 매핑 (CDSS → FHIR)"""
        mapping = {
            'M': 'male',
            'F': 'female',
            'O': 'other',
            'U': 'unknown'
        }
        return mapping.get(gender, 'unknown')


class EncounterConverter(FHIRConverter):
    """Encounter 리소스 컨버터"""

    @staticmethod
    def to_fhir(encounter) -> Dict:
        """
        Django Encounter 모델 → FHIR Encounter Resource

        Args:
            encounter: emr.models.Encounter 인스턴스

        Returns:
            FHIR Encounter Resource (dict)
        """
        resource = {
            "resourceType": "Encounter",
            "id": encounter.encounter_id,
            "meta": FHIRConverter.get_meta("Encounter", encounter.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/encounter",
                    encounter.encounter_id
                )
            ],
            "status": EncounterConverter._map_status(encounter.status),
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",  # Ambulatory (외래)
                "display": "ambulatory"
            },
            "subject": {
                "reference": f"Patient/{encounter.patient.patient_id}",
                "display": f"{encounter.patient.last_name} {encounter.patient.first_name}"
            },
            "period": {
                "start": encounter.encounter_date.isoformat() if encounter.encounter_date else None
            }
        }

        # 진료 사유 (reason)
        if encounter.reason:
            resource["reasonCode"] = [{
                "text": encounter.reason
            }]

        return resource

    @staticmethod
    def _map_status(status: str) -> str:
        """진료 상태 매핑 (CDSS → FHIR)"""
        mapping = {
            'scheduled': 'planned',
            'in_progress': 'in-progress',
            'completed': 'finished',
            'cancelled': 'cancelled'
        }
        return mapping.get(status, 'unknown')


class ObservationConverter(FHIRConverter):
    """Observation 리소스 컨버터 (검사 결과)"""

    @staticmethod
    def to_fhir(lab_result) -> Dict:
        """
        Django LabResult 모델 → FHIR Observation Resource

        Args:
            lab_result: lis.models.LabResult 인스턴스

        Returns:
            FHIR Observation Resource (dict)
        """
        from lis.models import LabResult  # Avoid circular import

        resource = {
            "resourceType": "Observation",
            "id": str(lab_result.result_id),
            "meta": FHIRConverter.get_meta("Observation"),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/observation",
                    str(lab_result.result_id)
                )
            ],
            "status": "final",  # LabResult는 보고된 상태이므로 final
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": lab_result.test_master.test_code,
                    "display": lab_result.test_master.test_name
                }],
                "text": lab_result.test_master.test_name
            },
            "subject": {
                "reference": f"Patient/{lab_result.patient.patient_id}"
            },
            "effectiveDateTime": lab_result.reported_at.isoformat()
        }

        # Value (결과 값)
        if lab_result.result_value:
            try:
                # 숫자형 결과인 경우
                resource["valueQuantity"] = {
                    "value": float(lab_result.result_value),
                    "unit": lab_result.result_unit or lab_result.test_master.unit or "",
                    "system": "http://unitsofmeasure.org"
                }
            except (ValueError, TypeError):
                # 텍스트 결과인 경우
                resource["valueString"] = lab_result.result_value

        # Reference Range (정상 범위)
        if lab_result.test_master.reference_range:
            resource["referenceRange"] = [{
                "text": lab_result.test_master.reference_range
            }]

        # Interpretation (해석 - 정상/비정상)
        if lab_result.is_abnormal:
            code = "H" if lab_result.abnormal_flag == "H" else "L" if lab_result.abnormal_flag == "L" else "A"
            display = "High" if code == "H" else "Low" if code == "L" else "Abnormal"
            resource["interpretation"] = [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": code,
                    "display": display
                }]
            }]

        return resource


class DiagnosticReportConverter(FHIRConverter):
    """DiagnosticReport 리소스 컨버터 (AI 분석 결과)"""

    @staticmethod
    def to_fhir(ai_job) -> Dict:
        """
        Django AIJob 모델 → FHIR DiagnosticReport Resource

        Args:
            ai_job: ai.models.AIJob 인스턴스

        Returns:
            FHIR DiagnosticReport Resource (dict)
        """
        resource = {
            "resourceType": "DiagnosticReport",
            "id": str(ai_job.job_id),
            "meta": FHIRConverter.get_meta("DiagnosticReport", ai_job.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/diagnosticreport",
                    str(ai_job.job_id)
                )
            ],
            "status": DiagnosticReportConverter._map_status(ai_job.status),
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "RAD",
                    "display": "Radiology"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "18748-4",
                    "display": "Diagnostic imaging study"
                }],
                "text": f"AI Analysis: {ai_job.analysis_type}"
            },
            "subject": {
                "reference": f"Patient/{ai_job.patient.patient_id}"
            },
            "effectiveDateTime": ai_job.started_at.isoformat() if ai_job.started_at else None,
            "issued": ai_job.completed_at.isoformat() if ai_job.completed_at else None
        }

        # Conclusion (AI 분석 결과)
        if ai_job.result:
            resource["conclusion"] = ai_job.result.get('summary', 'AI analysis completed')

            # Coded Diagnosis (진단 코드)
            if ai_job.result.get('diagnosis_code'):
                resource["conclusionCode"] = [{
                    "coding": [{
                        "system": "http://hl7.org/fhir/sid/icd-10",
                        "code": ai_job.result['diagnosis_code'],
                        "display": ai_job.result.get('diagnosis_name', '')
                    }]
                }]

        # Result (관련 Observation 참조)
        if ai_job.result and ai_job.result.get('confidence'):
            resource["result"] = [{
                "display": f"Confidence: {ai_job.result['confidence']}%"
            }]

        return resource

    @staticmethod
    def _map_status(status: str) -> str:
        """AI 작업 상태 매핑"""
        mapping = {
            'pending': 'registered',
            'processing': 'partial',
            'completed': 'final',
            'failed': 'cancelled',
            'under_review': 'preliminary'
        }
        return mapping.get(status, 'unknown')

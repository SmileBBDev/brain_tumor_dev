"""
FHIR Extended Converters

추가 FHIR R4 리소스 변환기 (5개)
- MedicationRequest: 약물 처방
- ServiceRequest: 검사/시술 요청
- Condition: 진단 정보
- ImagingStudy: 영상 검사
- Procedure: 시술 절차
"""
from typing import Dict
from django.conf import settings
from .converters import FHIRConverter


class MedicationRequestConverter(FHIRConverter):
    """MedicationRequest 리소스 컨버터 (약물 처방)"""

    @staticmethod
    def to_fhir(order) -> Dict:
        """
        Django Order 모델 → FHIR MedicationRequest Resource

        Args:
            order: emr.models.Order 인스턴스 (order_type='medication')

        Returns:
            FHIR MedicationRequest Resource (dict)
        """
        resource = {
            "resourceType": "MedicationRequest",
            "id": order.order_id,
            "meta": FHIRConverter.get_meta("MedicationRequest", order.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/medicationrequest",
                    order.order_id
                )
            ],
            "status": MedicationRequestConverter._map_status(order.status),
            "intent": "order",
            "priority": MedicationRequestConverter._map_priority(order.urgency),
            "subject": {
                "reference": f"Patient/{order.patient.patient_id}",
                "display": order.patient.full_name
            },
            "authoredOn": order.created_at.isoformat(),
            "requester": {
                "reference": f"Practitioner/{order.doctor_id}"
            }
        }

        # Medication (약물 정보)
        medication_text = "Medication order"
        if order.instructions:
            medication_text = order.instructions

        resource["medicationCodeableConcept"] = {
            "text": medication_text
        }

        # Dosage Instruction
        if order.instructions:
            resource["dosageInstruction"] = [{
                "text": order.instructions,
                "timing": {
                    "repeat": {
                        "frequency": 1,
                        "period": 1,
                        "periodUnit": "d"
                    }
                }
            }]

        # Encounter
        if order.encounter_id:
            resource["encounter"] = {
                "reference": f"Encounter/{order.encounter_id}"
            }

        return resource

    @staticmethod
    def _map_status(status: str) -> str:
        """처방 상태 매핑"""
        mapping = {
            'pending': 'active',
            'approved': 'active',
            'in_progress': 'active',
            'completed': 'completed',
            'cancelled': 'cancelled'
        }
        return mapping.get(status, 'unknown')

    @staticmethod
    def _map_priority(urgency: str) -> str:
        """우선순위 매핑"""
        mapping = {
            'routine': 'routine',
            'urgent': 'urgent',
            'stat': 'stat'
        }
        return mapping.get(urgency, 'routine')


class ServiceRequestConverter(FHIRConverter):
    """ServiceRequest 리소스 컨버터 (검사/시술 요청)"""

    @staticmethod
    def to_fhir(order) -> Dict:
        """
        Django Order/RadiologyOrder 모델 → FHIR ServiceRequest Resource

        Args:
            order: emr.models.Order 또는 ris.models.RadiologyOrder 인스턴스

        Returns:
            FHIR ServiceRequest Resource (dict)
        """
        # RadiologyOrder인지 Order인지 구분
        is_radiology = hasattr(order, 'modality')

        order_id = str(order.order_id) if is_radiology else order.order_id

        resource = {
            "resourceType": "ServiceRequest",
            "id": order_id,
            "meta": FHIRConverter.get_meta("ServiceRequest", order.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/servicerequest",
                    order_id
                )
            ],
            "status": ServiceRequestConverter._map_status(order.status),
            "intent": "order",
            "priority": ServiceRequestConverter._map_priority(
                order.priority if is_radiology else order.urgency
            ),
            "subject": {
                "reference": f"Patient/{order.patient_id if is_radiology else order.patient.patient_id}"
            },
            "authoredOn": order.created_at.isoformat()
        }

        # Category (검사 유형)
        if is_radiology:
            resource["category"] = [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "363679005",
                    "display": "Imaging"
                }]
            }]
            resource["code"] = {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": order.modality,
                    "display": f"{order.modality} study"
                }],
                "text": f"{order.modality} - {order.body_part}"
            }
            if order.clinical_info:
                resource["reasonCode"] = [{
                    "text": order.clinical_info
                }]
            # Requester
            if hasattr(order, 'ordered_by') and order.ordered_by:
                resource["requester"] = {
                    "reference": f"Practitioner/{order.ordered_by.user_id}"
                }
        else:
            category_code = "108252007" if order.order_type == 'lab' else "387713003"
            category_display = "Laboratory procedure" if order.order_type == 'lab' else "Surgical procedure"
            resource["category"] = [{
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": category_code,
                    "display": category_display
                }]
            }]
            resource["code"] = {
                "text": f"{order.order_type} order"
            }
            # Requester
            if hasattr(order, 'doctor_id'):
                resource["requester"] = {
                    "reference": f"Practitioner/{order.doctor_id}"
                }

        return resource

    @staticmethod
    def _map_status(status: str) -> str:
        """상태 매핑"""
        mapping = {
            'pending': 'active',
            'ORDERED': 'active',
            'approved': 'active',
            'SCHEDULED': 'active',
            'in_progress': 'active',
            'IN_PROGRESS': 'active',
            'completed': 'completed',
            'COMPLETED': 'completed',
            'cancelled': 'revoked',
            'CANCELLED': 'revoked'
        }
        return mapping.get(status, 'unknown')

    @staticmethod
    def _map_priority(priority: str) -> str:
        """우선순위 매핑"""
        mapping = {
            'routine': 'routine',
            'ROUTINE': 'routine',
            'urgent': 'urgent',
            'URGENT': 'urgent',
            'stat': 'stat',
            'STAT': 'stat'
        }
        return mapping.get(priority, 'routine')


class ConditionConverter(FHIRConverter):
    """Condition 리소스 컨버터 (진단 정보)"""

    @staticmethod
    def to_fhir(encounter_diagnosis) -> Dict:
        """
        Django EncounterDiagnosis 모델 → FHIR Condition Resource

        Args:
            encounter_diagnosis: emr.models.EncounterDiagnosis 인스턴스

        Returns:
            FHIR Condition Resource (dict)
        """
        condition_id = f"{encounter_diagnosis.encounter.encounter_id}-{encounter_diagnosis.id}"

        resource = {
            "resourceType": "Condition",
            "id": condition_id,
            "meta": FHIRConverter.get_meta("Condition", encounter_diagnosis.created_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/condition",
                    condition_id
                )
            ],
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "encounter-diagnosis",
                    "display": "Encounter Diagnosis"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": encounter_diagnosis.diag_code,
                    "display": encounter_diagnosis.diagnosis_name
                }],
                "text": encounter_diagnosis.diagnosis_name
            },
            "subject": {
                "reference": f"Patient/{encounter_diagnosis.encounter.patient.patient_id}",
                "display": encounter_diagnosis.encounter.patient.full_name
            },
            "encounter": {
                "reference": f"Encounter/{encounter_diagnosis.encounter.encounter_id}"
            },
            "recordedDate": encounter_diagnosis.created_at.isoformat()
        }

        # Priority (주진단/부진단)
        if encounter_diagnosis.priority == 1:
            resource["category"][0]["coding"].append({
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": "problem-list-item",
                "display": "Problem List Item"
            })

        # Comments
        if encounter_diagnosis.comments:
            resource["note"] = [{
                "text": encounter_diagnosis.comments
            }]

        return resource


class ImagingStudyConverter(FHIRConverter):
    """ImagingStudy 리소스 컨버터 (영상 검사)"""

    @staticmethod
    def to_fhir(radiology_study) -> Dict:
        """
        Django RadiologyStudy 모델 → FHIR ImagingStudy Resource

        Args:
            radiology_study: ris.models.RadiologyStudy 인스턴스

        Returns:
            FHIR ImagingStudy Resource (dict)
        """
        resource = {
            "resourceType": "ImagingStudy",
            "id": str(radiology_study.study_id),
            "meta": FHIRConverter.get_meta("ImagingStudy", radiology_study.synced_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/imagingstudy",
                    str(radiology_study.study_id)
                ),
                {
                    "system": "urn:dicom:uid",
                    "value": f"urn:oid:{radiology_study.study_instance_uid}"
                }
            ],
            "status": "available",
            "subject": {
                "reference": f"Patient/{radiology_study.patient_id}",
                "display": radiology_study.patient_name
            },
            "numberOfSeries": radiology_study.num_series,
            "numberOfInstances": radiology_study.num_instances
        }

        # Started datetime
        if radiology_study.study_date and radiology_study.study_time:
            resource["started"] = f"{radiology_study.study_date}T{radiology_study.study_time}"

        # Modality
        if radiology_study.modality:
            resource["modality"] = [{
                "system": "http://dicom.nema.org/resources/ontology/DCM",
                "code": radiology_study.modality
            }]

        # Description
        if radiology_study.study_description:
            resource["description"] = radiology_study.study_description

        # Referrer
        if radiology_study.referring_physician:
            resource["referrer"] = {
                "display": radiology_study.referring_physician
            }

        # Endpoint (WADO-RS)
        orthanc_url = getattr(settings, 'ORTHANC_API_URL', 'http://localhost:8042')
        resource["endpoint"] = [{
            "reference": f"{orthanc_url}/dicom-web/studies/{radiology_study.study_instance_uid}"
        }]

        # BasedOn (관련 ServiceRequest)
        if radiology_study.order:
            resource["basedOn"] = [{
                "reference": f"ServiceRequest/{radiology_study.order.order_id}"
            }]

        return resource


class ProcedureConverter(FHIRConverter):
    """Procedure 리소스 컨버터 (시술/검사 절차)"""

    @staticmethod
    def to_fhir(order) -> Dict:
        """
        Django Order 모델 → FHIR Procedure Resource

        Args:
            order: emr.models.Order 인스턴스 (order_type='procedure')

        Returns:
            FHIR Procedure Resource (dict)
        """
        resource = {
            "resourceType": "Procedure",
            "id": order.order_id,
            "meta": FHIRConverter.get_meta("Procedure", order.updated_at),
            "identifier": [
                FHIRConverter.get_identifier(
                    f"{settings.FHIR_SERVER_URL}/identifier/procedure",
                    order.order_id
                )
            ],
            "status": ProcedureConverter._map_status(order.status),
            "subject": {
                "reference": f"Patient/{order.patient.patient_id}",
                "display": order.patient.full_name
            }
        }

        # PerformedDateTime
        if order.status == 'completed':
            resource["performedDateTime"] = order.updated_at.isoformat()

        # Category
        resource["category"] = {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "387713003",
                "display": "Surgical procedure"
            }]
        }

        # Code (시술 코드)
        if order.order_type:
            resource["code"] = {
                "text": f"{order.order_type.upper()} procedure"
            }

        # Encounter
        if order.encounter_id:
            resource["encounter"] = {
                "reference": f"Encounter/{order.encounter_id}"
            }

        # Performer
        if order.doctor_id:
            resource["performer"] = [{
                "actor": {
                    "reference": f"Practitioner/{order.doctor_id}"
                }
            }]

        # Note
        if order.instructions:
            resource["note"] = [{
                "text": order.instructions
            }]

        return resource

    @staticmethod
    def _map_status(status: str) -> str:
        """시술 상태 매핑"""
        mapping = {
            'pending': 'preparation',
            'approved': 'preparation',
            'in_progress': 'in-progress',
            'completed': 'completed',
            'cancelled': 'stopped'
        }
        return mapping.get(status, 'unknown')

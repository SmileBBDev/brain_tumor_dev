"""
OpenEMR FHIR Mapper

Django 모델과 OpenEMR FHIR 리소스 간 변환을 담당합니다.

데이터 흐름:
- PatientCache (Django MySQL 기본 정보) ↔ OpenEMR Patient (FHIR 상세 정보)
- Encounter (Django MySQL 기본 정보) ↔ OpenEMR Encounter (FHIR 상세 정보)
- Order (Django MySQL 기본 정보) ↔ OpenEMR MedicationRequest (FHIR 상세 정보)
"""

from typing import Dict, Any, Optional
from datetime import datetime


def patient_cache_to_openemr_patient(patient_cache) -> Dict[str, Any]:
    """
    PatientCache 모델 → OpenEMR FHIR Patient Resource (상세 정보 포함)

    Args:
        patient_cache: emr.models.PatientCache 인스턴스

    Returns:
        dict: FHIR Patient resource for OpenEMR (상세 정보 포함)
    """
    # Emergency contact 처리
    contact = []
    if patient_cache.emergency_contact:
        contact.append({
            'relationship': [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0131',
                            'code': 'C',
                            'display': 'Emergency Contact',
                        }
                    ],
                    'text': patient_cache.emergency_contact.get('relationship', 'Emergency Contact')
                }
            ],
            'name': {
                'text': patient_cache.emergency_contact.get('name', ''),
            },
            'telecom': [
                {
                    'system': 'phone',
                    'value': patient_cache.emergency_contact.get('phone', ''),
                }
            ],
        })

    # Telecom (phone, email)
    telecom = []
    if patient_cache.phone:
        telecom.append({
            'system': 'phone',
            'value': patient_cache.phone,
            'use': 'mobile',
        })
    if patient_cache.email:
        telecom.append({
            'system': 'email',
            'value': patient_cache.email,
        })

    # Address
    address = []
    if patient_cache.address:
        address.append({
            'use': 'home',
            'text': patient_cache.address,
        })

    # Extension for additional fields
    extension = []

    # Blood type extension
    if patient_cache.blood_type:
        extension.append({
            'url': 'http://neuronova.com/fhir/StructureDefinition/blood-type',
            'valueString': patient_cache.blood_type,
        })

    # Allergies extension
    if patient_cache.allergies:
        extension.append({
            'url': 'http://neuronova.com/fhir/StructureDefinition/allergies',
            'valueString': ', '.join(patient_cache.allergies) if isinstance(patient_cache.allergies, list) else str(patient_cache.allergies),
        })

    # SSN extension (주민등록번호)
    if patient_cache.ssn:
        extension.append({
            'url': 'http://neuronova.com/fhir/StructureDefinition/ssn',
            'valueString': patient_cache.ssn,
        })

    # Helper for safe isoformat
    def safe_isoformat(val):
        if not val:
            return None
        if isinstance(val, str):
            return val
        return val.isoformat()

    patient_resource = {
        'resourceType': 'Patient',
        'identifier': [
            {
                'system': 'http://neuronova.com/patient-id',
                'value': patient_cache.patient_id,
            }
        ],
        'active': True,
        'name': [
            {
                'use': 'official',
                'family': patient_cache.family_name,
                'given': [patient_cache.given_name],
            }
        ],
        'telecom': telecom,
        'gender': patient_cache.gender,  # FHIR 형식 (male, female, other, unknown)
        'birthDate': safe_isoformat(patient_cache.birth_date),
        'address': address,
        'contact': contact,
    }

    # Extension이 있으면 추가
    if extension:
        patient_resource['extension'] = extension

    return patient_resource


def openemr_patient_to_dict(openemr_patient: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenEMR FHIR Patient Resource → 딕셔너리 (상세 정보 추출)

    Args:
        openemr_patient: OpenEMR에서 가져온 FHIR Patient resource

    Returns:
        dict: 상세 정보가 담긴 딕셔너리
    """
    detail = {
        'openemr_patient_id': openemr_patient.get('id'),
        'active': openemr_patient.get('active', True),
    }

    # Extension 정보 추출
    extensions = openemr_patient.get('extension', [])
    for ext in extensions:
        url = ext.get('url', '')

        if 'blood-type' in url:
            detail['blood_type'] = ext.get('valueString')
        elif 'allergies' in url:
            allergies_str = ext.get('valueString', '')
            detail['allergies'] = [a.strip() for a in allergies_str.split(',')] if allergies_str else []
        elif 'ssn' in url:
            detail['ssn'] = ext.get('valueString')
        elif 'marital-status' in url:
            detail['marital_status'] = ext.get('valueCodeableConcept', {}).get('text')
        elif 'occupation' in url:
            detail['occupation'] = ext.get('valueString')

    # Communication (선호 언어)
    communication = openemr_patient.get('communication', [])
    if communication:
        detail['preferred_language'] = communication[0].get('language', {}).get('text')

    # General Practitioner (주치의)
    general_practitioner = openemr_patient.get('generalPractitioner', [])
    if general_practitioner:
        detail['general_practitioner'] = general_practitioner[0].get('display')

    # Managing Organization (관리 기관)
    managing_org = openemr_patient.get('managingOrganization', {})
    if managing_org:
        detail['managing_organization'] = managing_org.get('display')

    # Contact (응급 연락처 외 추가 연락처)
    contacts = openemr_patient.get('contact', [])
    detail['additional_contacts'] = []
    for contact in contacts:
        contact_info = {
            'name': contact.get('name', {}).get('text'),
            'relationship': contact.get('relationship', [{}])[0].get('text'),
            'telecom': []
        }
        for telecom in contact.get('telecom', []):
            contact_info['telecom'].append({
                'system': telecom.get('system'),
                'value': telecom.get('value'),
            })
        detail['additional_contacts'].append(contact_info)

    return detail


def encounter_to_openemr_encounter(encounter) -> Dict[str, Any]:
    """
    Encounter 모델 → OpenEMR FHIR Encounter Resource

    Args:
        encounter: emr.models.Encounter 인스턴스

    Returns:
        dict: FHIR Encounter resource for OpenEMR
    """
    # Status 매핑 (Django → FHIR)
    status_map = {
        'scheduled': 'planned',
        'in_progress': 'in-progress',
        'completed': 'finished',
        'cancelled': 'cancelled',
    }

    # Class 매핑 (encounter_type → FHIR class)
    class_map = {
        'outpatient': {'code': 'AMB', 'display': 'ambulatory'},
        'emergency': {'code': 'EMER', 'display': 'emergency'},
        'inpatient': {'code': 'IMP', 'display': 'inpatient encounter'},
        'discharge': {'code': 'IMP', 'display': 'inpatient encounter'},
    }

    encounter_class = class_map.get(encounter.encounter_type, {'code': 'AMB', 'display': 'ambulatory'})

    encounter_resource = {
        'resourceType': 'Encounter',
        'identifier': [
            {
                'system': 'http://neuronova.com/encounter-id',
                'value': encounter.encounter_id,
            }
        ],
        'status': status_map.get(encounter.status, 'unknown'),
        'class': {
            'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
            'code': encounter_class['code'],
            'display': encounter_class['display'],
        },
        'subject': {
            'reference': f"Patient/{encounter.patient.openemr_patient_id}" if encounter.patient.openemr_patient_id else None,
            'display': encounter.patient.full_name,
        },
        'participant': [
            {
                'type': [
                    {
                        'coding': [
                            {
                                'system': 'http://terminology.hl7.org/CodeSystem/v3-ParticipationType',
                                'code': 'ATND',
                                'display': 'attender',
                            }
                        ]
                    }
                ],
                'individual': {
                    'reference': f"Practitioner/{encounter.doctor_id}",
                }
            }
        ],
        'period': {
            'start': encounter.encounter_date.isoformat() if encounter.encounter_date else None,
        },
        'reasonCode': [
            {
                'text': encounter.chief_complaint,
            }
        ] if encounter.chief_complaint else [],
        'serviceProvider': {
            'display': encounter.department,
        },
    }

    # Diagnosis (진단)
    if encounter.diagnosis:
        encounter_resource['diagnosis'] = [
            {
                'condition': {
                    'display': encounter.diagnosis,
                }
            }
        ]

    return encounter_resource


def openemr_encounter_to_dict(openemr_encounter: Dict[str, Any]) -> Dict[str, Any]:
    """
    OpenEMR FHIR Encounter Resource → 딕셔너리 (상세 정보 추출)

    Args:
        openemr_encounter: OpenEMR에서 가져온 FHIR Encounter resource

    Returns:
        dict: 상세 정보가 담긴 딕셔너리
    """
    detail = {
        'openemr_encounter_id': openemr_encounter.get('id'),
        'status': openemr_encounter.get('status'),
        'class_code': openemr_encounter.get('class', {}).get('code'),
        'class_display': openemr_encounter.get('class', {}).get('display'),
    }

    # Period (시작/종료 시간)
    period = openemr_encounter.get('period', {})
    if period:
        detail['period_start'] = period.get('start')
        detail['period_end'] = period.get('end')

    # Hospitalization (입원 정보)
    hospitalization = openemr_encounter.get('hospitalization', {})
    if hospitalization:
        detail['admission_source'] = hospitalization.get('admitSource', {}).get('text')
        detail['discharge_disposition'] = hospitalization.get('dischargeDisposition', {}).get('text')

    # Location (위치 정보)
    locations = openemr_encounter.get('location', [])
    if locations:
        detail['locations'] = [
            {
                'name': loc.get('location', {}).get('display'),
                'status': loc.get('status'),
            }
            for loc in locations
        ]

    # Service type (진료 유형)
    service_type = openemr_encounter.get('serviceType', {})
    if service_type:
        detail['service_type'] = service_type.get('text')

    return detail


def order_to_openemr_medication_request(order) -> Dict[str, Any]:
    """
    Order 모델 → OpenEMR FHIR MedicationRequest Resource

    Args:
        order: emr.models.Order 인스턴스

    Returns:
        dict: FHIR MedicationRequest resource for OpenEMR
    """
    # Status 매핑
    status_map = {
        'pending': 'draft',
        'approved': 'active',
        'in_progress': 'active',
        'completed': 'completed',
        'cancelled': 'cancelled',
    }

    # Priority 매핑
    priority_map = {
        'routine': 'routine',
        'urgent': 'urgent',
        'stat': 'stat',
    }

    medication_request = {
        'resourceType': 'MedicationRequest',
        'identifier': [
            {
                'system': 'http://neuronova.com/order-id',
                'value': order.order_id,
            }
        ],
        'status': status_map.get(order.status, 'draft'),
        'intent': 'order',
        'priority': priority_map.get(order.urgency, 'routine'),
        'subject': {
            'reference': f"Patient/{order.patient.openemr_patient_id}" if order.patient.openemr_patient_id else None,
            'display': order.patient.full_name,
        },
        'encounter': {
            'reference': f"Encounter/{order.encounter.openemr_encounter_id}" if order.encounter and hasattr(order.encounter, 'openemr_encounter_id') else None,
        } if order.encounter else None,
        'authoredOn': order.ordered_at.isoformat() if order.ordered_at else None,
        'requester': {
            'reference': f"Practitioner/{order.ordered_by}",
        },
        'note': [
            {
                'text': order.notes,
            }
        ] if order.notes else [],
    }

    # OrderItem (약물 상세) 추가
    if hasattr(order, 'items') and order.items.exists():
        # 첫 번째 약물을 메인으로
        first_item = order.items.first()
        medication_request['medicationCodeableConcept'] = {
            'coding': [
                {
                    'system': 'http://neuronova.com/medication-code',
                    'code': first_item.drug_code if first_item.drug_code else '',
                    'display': first_item.drug_name,
                }
            ],
            'text': first_item.drug_name,
        }

        # Dosage instruction
        medication_request['dosageInstruction'] = [
            {
                'text': f"{first_item.dosage} {first_item.frequency} for {first_item.duration}",
                'route': {
                    'text': first_item.route,
                },
                'doseAndRate': [
                    {
                        'doseQuantity': {
                            'value': first_item.dosage,
                        }
                    }
                ],
                'additionalInstruction': [
                    {
                        'text': first_item.instructions,
                    }
                ] if first_item.instructions else [],
            }
        ]

    return medication_request

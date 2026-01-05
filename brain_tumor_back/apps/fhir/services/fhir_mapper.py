"""
FHIR Resource Mappers

Django 모델을 FHIR R4 리소스로 변환합니다.
"""

from datetime import datetime


def patient_to_fhir(patient_cache):
    """
    PatientCache 모델 → FHIR Patient Resource

    Args:
        patient_cache: emr.models.PatientCache 인스턴스

    Returns:
        dict: FHIR Patient resource
    """
    # Emergency contact 처리
    emergency_contact = []
    if patient_cache.emergency_contact:
        emergency_contact = [{
            'relationship': [
                {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org/CodeSystem/v2-0131',
                            'code': 'E',
                            'display': 'Emergency Contact',
                        }
                    ]
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
        }]

    return {
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
        'telecom': [
            {
                'system': 'phone',
                'value': patient_cache.phone,
                'use': 'mobile',
            } if patient_cache.phone else None,
            {
                'system': 'email',
                'value': patient_cache.email,
            } if patient_cache.email else None,
        ],
        'gender': patient_cache.gender,  # 이미 FHIR 형식 (male, female, other, unknown)
        'birthDate': patient_cache.birth_date.isoformat() if patient_cache.birth_date and not isinstance(patient_cache.birth_date, str) else patient_cache.birth_date,
        'address': [
            {
                'use': 'home',
                'text': patient_cache.address,
            }
        ] if patient_cache.address else [],
        'contact': emergency_contact,
    }


def prescription_to_fhir(prescription):
    """
    Prescription 모델 → FHIR MedicationRequest Resource

    Args:
        prescription: ocs.models.Prescription 인스턴스

    Returns:
        dict: FHIR MedicationRequest resource
    """
    # Prescription items를 medicationCodeableConcept으로 변환
    medications = []
    for item in prescription.items.all():
        medications.append({
            'medicationCodeableConcept': {
                'coding': [
                    {
                        'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                        'display': item.medication_name,
                    }
                ],
                'text': f'{item.medication_name} {item.dosage} {item.form}',
            },
            'dosageInstruction': [
                {
                    'text': item.instructions,
                    'timing': {
                        'repeat': {
                            'duration': item.duration_days,
                            'durationUnit': 'd',
                        }
                    },
                    'route': {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'display': item.form,
                            }
                        ]
                    },
                }
            ],
            'dispenseRequest': {
                'quantity': {
                    'value': item.quantity,
                    'unit': item.form,
                }
            },
        })

    # 첫 번째 약물을 기본으로 (또는 통합)
    first_med = medications[0] if medications else {}

    return {
        'resourceType': 'MedicationRequest',
        'status': prescription.status.lower() if prescription.status else 'active',
        'intent': 'order',
        'priority': 'routine',
        'subject': {
            'reference': f'Patient/{prescription.patient.fhir_id}' if prescription.patient.fhir_id else None,
            'display': prescription.patient.get_full_name(),
        },
        'authoredOn': prescription.prescribed_date.isoformat() if prescription.prescribed_date else datetime.now().isoformat(),
        'requester': {
            'display': prescription.prescribed_by.get_full_name() if prescription.prescribed_by else 'Unknown',
        },
        'reasonCode': [
            {
                'text': prescription.diagnosis,
            }
        ] if prescription.diagnosis else [],
        'note': [
            {
                'text': prescription.notes,
            }
        ] if prescription.notes else [],
        **first_med,  # Merge first medication details
    }


def lab_test_to_fhir(lab_test):
    """
    LabTest 모델 → FHIR DiagnosticReport Resource

    Args:
        lab_test: lis.models.LabTest 인스턴스

    Returns:
        dict: FHIR DiagnosticReport resource
    """
    return {
        'resourceType': 'DiagnosticReport',
        'status': lab_test.status.lower() if lab_test.status else 'final',
        'category': [
            {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0074',
                        'code': 'LAB',
                        'display': 'Laboratory',
                    }
                ]
            }
        ],
        'code': {
            'coding': [
                {
                    'system': 'http://loinc.org',
                    'code': lab_test.test_code,
                    'display': lab_test.test_name,
                }
            ],
            'text': lab_test.test_name,
        },
        'subject': {
            'reference': f'Patient/{lab_test.patient.fhir_id}' if lab_test.patient.fhir_id else None,
            'display': lab_test.patient.get_full_name(),
        },
        'effectiveDateTime': lab_test.performed_date.isoformat() if lab_test.performed_date else None,
        'issued': datetime.now().isoformat(),
        'performer': [
            {
                'display': lab_test.performed_by.get_full_name() if lab_test.performed_by else 'Unknown',
            }
        ] if lab_test.performed_by else [],
        'result': [],  # Will be populated with Observation references
    }


def lab_result_to_fhir(lab_result, lab_test):
    """
    LabResult 모델 → FHIR Observation Resource

    Args:
        lab_result: lis.models.LabResult 인스턴스
        lab_test: lis.models.LabTest 인스턴스 (parent)

    Returns:
        dict: FHIR Observation resource
    """
    # Flag interpretation
    interpretation = None
    if lab_result.flag:
        if lab_result.flag in ['HIGH', 'H']:
            interpretation = 'H'
        elif lab_result.flag in ['LOW', 'L']:
            interpretation = 'L'
        elif lab_result.flag == 'NORMAL':
            interpretation = 'N'
        elif lab_result.flag in ['CRITICAL', 'PANIC']:
            interpretation = 'A'  # Abnormal

    return {
        'resourceType': 'Observation',
        'status': 'final',
        'category': [
            {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                        'code': 'laboratory',
                        'display': 'Laboratory',
                    }
                ]
            }
        ],
        'code': {
            'coding': [
                {
                    'system': 'http://loinc.org',
                    'display': lab_result.test_name,
                }
            ],
            'text': lab_result.test_name,
        },
        'subject': {
            'reference': f'Patient/{lab_test.patient.fhir_id}' if lab_test.patient.fhir_id else None,
            'display': lab_test.patient.get_full_name(),
        },
        'effectiveDateTime': lab_test.performed_date.isoformat() if lab_test.performed_date else None,
        'issued': datetime.now().isoformat(),
        'valueQuantity': {
            'value': float(lab_result.value) if lab_result.value and lab_result.value.replace('.', '').isdigit() else None,
            'unit': lab_result.unit,
        } if lab_result.unit else None,
        'valueString': lab_result.value if not (lab_result.value and lab_result.value.replace('.', '').isdigit()) else None,
        'interpretation': [
            {
                'coding': [
                    {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                        'code': interpretation,
                    }
                ]
            }
        ] if interpretation else [],
        'referenceRange': [
            {
                'text': lab_result.reference_range,
            }
        ] if lab_result.reference_range else [],
    }

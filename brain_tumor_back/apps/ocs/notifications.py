"""
OCS 알림 서비스
- OCS 상태 변경 시 WebSocket을 통해 관련 사용자에게 알림 전송
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone


def notify_ocs_status_changed(ocs, from_status, to_status, actor):
    """
    OCS 상태 변경 알림 전송

    Args:
        ocs: OCS 인스턴스
        from_status: 이전 상태
        to_status: 변경된 상태
        actor: 상태 변경을 수행한 사용자
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    timestamp = timezone.now().isoformat()

    # 상태별 메시지
    status_messages = {
        'ACCEPTED': f'{ocs.patient.name}님의 {ocs.job_type} 오더가 접수되었습니다.',
        'IN_PROGRESS': f'{ocs.patient.name}님의 {ocs.job_type} 작업이 시작되었습니다.',
        'RESULT_READY': f'{ocs.patient.name}님의 {ocs.job_type} 결과가 제출되었습니다.',
        'CONFIRMED': f'{ocs.patient.name}님의 {ocs.job_type} 결과가 확정되었습니다.',
        'CANCELLED': f'{ocs.patient.name}님의 {ocs.job_type} 오더가 취소되었습니다.',
    }

    message = status_messages.get(to_status, f'OCS 상태가 {to_status}(으)로 변경되었습니다.')

    event_data = {
        'type': 'ocs_status_changed',
        'ocs_id': ocs.ocs_id,
        'ocs_pk': ocs.id,
        'from_status': from_status,
        'to_status': to_status,
        'job_role': ocs.job_role,
        'patient_name': ocs.patient.name,
        'actor_name': actor.name if actor else 'System',
        'message': message,
        'timestamp': timestamp,
    }

    # 담당 작업자에게 알림 (RIS/LIS 개인별 그룹)
    job_role_lower = ocs.job_role.lower() if ocs.job_role else ''
    if job_role_lower in ['ris', 'lis'] and ocs.worker_id:
        async_to_sync(channel_layer.group_send)(f"ocs_{job_role_lower}_{ocs.worker_id}", event_data)

    # 처방 의사에게 알림 (의사 전용 그룹)
    if ocs.doctor_id:
        async_to_sync(channel_layer.group_send)(f"ocs_doctor_{ocs.doctor_id}", event_data)


def notify_ocs_created(ocs, doctor):
    """
    새 OCS 생성 알림 전송

    Args:
        ocs: OCS 인스턴스
        doctor: 오더를 생성한 의사
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    timestamp = timezone.now().isoformat()
    priority_label = {'urgent': '긴급', 'normal': '일반', 'scheduled': '예약'}.get(ocs.priority, ocs.priority)

    message = f'새 {ocs.job_type} 오더가 생성되었습니다. (환자: {ocs.patient.name}, 우선순위: {priority_label})'

    event_data = {
        'type': 'ocs_created',
        'ocs_id': ocs.ocs_id,
        'ocs_pk': ocs.id,
        'job_role': ocs.job_role,
        'job_type': ocs.job_type,
        'priority': ocs.priority,
        'patient_name': ocs.patient.name,
        'doctor_name': doctor.name if doctor else 'Unknown',
        'message': message,
        'timestamp': timestamp,
    }

    # 담당 작업자에게 알림 (RIS/LIS 개인별 그룹)
    # 새로 생성된 OCS는 아직 worker가 없으므로 역할별 그룹으로 전송
    job_role_lower = ocs.job_role.lower() if ocs.job_role else ''
    if job_role_lower in ['ris', 'lis']:
        if ocs.worker_id:
            async_to_sync(channel_layer.group_send)(f"ocs_{job_role_lower}_{ocs.worker_id}", event_data)
        else:
            # 아직 담당자 미배정 → 역할별 그룹으로 전송 (모든 해당 역할 작업자가 수신)
            async_to_sync(channel_layer.group_send)(f"ocs_{job_role_lower}", event_data)


def notify_ocs_cancelled(ocs, actor, reason=''):
    """
    OCS 취소 알림 전송

    Args:
        ocs: OCS 인스턴스
        actor: 취소를 수행한 사용자
        reason: 취소 사유
    """
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    timestamp = timezone.now().isoformat()
    message = f'{ocs.patient.name}님의 {ocs.job_type} 오더가 취소되었습니다.'
    if reason:
        message += f' (사유: {reason})'

    event_data = {
        'type': 'ocs_cancelled',
        'ocs_id': ocs.ocs_id,
        'ocs_pk': ocs.id,
        'reason': reason,
        'actor_name': actor.name if actor else 'System',
        'message': message,
        'timestamp': timestamp,
    }

    # 담당 작업자에게 알림 (RIS/LIS 개인별 그룹)
    job_role_lower = ocs.job_role.lower() if ocs.job_role else ''
    if job_role_lower in ['ris', 'lis'] and ocs.worker_id:
        async_to_sync(channel_layer.group_send)(f"ocs_{job_role_lower}_{ocs.worker_id}", event_data)

    # 처방 의사에게 알림 (의사 전용 그룹)
    if ocs.doctor_id:
        async_to_sync(channel_layer.group_send)(f"ocs_doctor_{ocs.doctor_id}", event_data)

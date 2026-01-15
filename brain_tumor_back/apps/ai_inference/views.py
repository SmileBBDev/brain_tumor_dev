import logging
import httpx
import os
import mimetypes
from pathlib import Path
from django.utils import timezone
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.ocs.models import OCS
from .models import AIInference
from .serializers import InferenceRequestSerializer, InferenceCallbackSerializer, AIInferenceSerializer

logger = logging.getLogger(__name__)

# FastAPI modAI URL
FASTAPI_URL = "http://localhost:9000"


class M1InferenceView(APIView):
    """
    M1 추론 요청

    POST /api/ai/m1/inference/
    - ocs_id: MRI OCS ID
    - mode: 'manual' | 'auto'
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    def post(self, request):
        serializer = InferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ocs_id = serializer.validated_data['ocs_id']
        mode = serializer.validated_data.get('mode', 'manual')

        # 1. OCS 조회 및 검증
        try:
            ocs = OCS.objects.select_related('patient').get(id=ocs_id)
        except OCS.DoesNotExist:
            return Response(
                {'error': 'OCS를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. MRI 타입 검증
        if ocs.job_role != 'RIS' or ocs.job_type != 'MRI':
            return Response(
                {'error': 'M1 추론은 MRI OCS에서만 가능합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. DICOM 정보 검증 (study_uid만 필요, series는 FastAPI에서 자동 탐색)
        worker_result = ocs.worker_result or {}
        dicom_info = worker_result.get('dicom', {})
        study_uid = dicom_info.get('study_uid')

        if not study_uid:
            return Response(
                {'error': 'DICOM study_uid 정보가 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. 기존 완료된 추론 확인
        existing = AIInference.find_existing(
            model_type=AIInference.ModelType.M1,
            mri_ocs=ocs
        )

        if existing:
            # 캐시된 결과 반환
            logger.info(f'M1 캐시 결과 반환: ocs_id={ocs_id}, job_id={existing.job_id}')
            return Response({
                'job_id': existing.job_id,
                'status': 'completed',
                'cached': True,
                'message': '기존 추론 결과를 반환합니다.',
                'result': existing.result_data
            })

        # 5. 새 추론 생성
        inference = AIInference.objects.create(
            model_type=AIInference.ModelType.M1,
            patient=ocs.patient,
            mri_ocs=ocs,
            mode=mode,
            requested_by=request.user if request.user.is_authenticated else None,
            status=AIInference.Status.PENDING
        )

        # 6. FastAPI 호출 (study_uid로 시리즈 자동 탐색)
        try:
            callback_url = request.build_absolute_uri('/api/ai/callback/')

            response = httpx.post(
                f"{FASTAPI_URL}/api/v1/m1/inference",
                json={
                    'job_id': inference.job_id,
                    'study_uid': study_uid,
                    'patient_id': ocs.patient.patient_number,
                    'ocs_id': ocs_id,
                    'callback_url': callback_url,
                    'mode': mode,
                },
                timeout=30.0
            )
            response.raise_for_status()

            # 상태 업데이트
            inference.status = AIInference.Status.PROCESSING
            inference.save()

            return Response({
                'job_id': inference.job_id,
                'status': 'processing',
                'cached': False,
                'message': 'M1 추론이 시작되었습니다.'
            })

        except httpx.ConnectError:
            inference.status = AIInference.Status.FAILED
            inference.error_message = 'FastAPI 서버 연결 실패'
            inference.save()

            return Response(
                {'error': 'FastAPI 서버에 연결할 수 없습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except httpx.HTTPStatusError as e:
            inference.status = AIInference.Status.FAILED
            inference.error_message = str(e)
            inference.save()

            return Response(
                {'error': f'FastAPI 호출 실패: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MGInferenceView(APIView):
    """
    MG 추론 요청 (Gene Expression)

    POST /api/ai/mg/inference/
    - ocs_id: LIS OCS ID (Gene Expression CSV 포함)
    - mode: 'manual' | 'auto'
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    # CDSS_STORAGE 경로
    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE")

    def post(self, request):
        serializer = InferenceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ocs_id = serializer.validated_data['ocs_id']
        mode = serializer.validated_data.get('mode', 'manual')

        # 1. OCS 조회 및 검증
        try:
            ocs = OCS.objects.select_related('patient').get(id=ocs_id)
        except OCS.DoesNotExist:
            return Response(
                {'error': 'OCS를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. LIS 타입 검증
        if ocs.job_role != 'LIS':
            return Response(
                {'error': 'MG 추론은 LIS OCS에서만 가능합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Gene Expression CSV 파일 경로 추출
        worker_result = ocs.worker_result or {}
        files = worker_result.get('files', [])

        if not files:
            return Response(
                {'error': 'Gene Expression CSV 파일이 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 첫 번째 파일의 name 사용
        csv_filename = files[0].get('name')
        if not csv_filename:
            return Response(
                {'error': 'CSV 파일명을 찾을 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # CSV 파일 경로 구성 (OCS_XXXX 폴더명 형식 사용)
        folder_name = ocs.ocs_id.upper()  # ocs_0046 -> OCS_0046
        csv_path = self.STORAGE_BASE / "LIS" / folder_name / csv_filename

        if not csv_path.exists():
            return Response(
                {'error': f'CSV 파일을 찾을 수 없습니다: {csv_path}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. 기존 완료된 추론 확인
        existing = AIInference.find_existing(
            model_type=AIInference.ModelType.MG,
            rna_ocs=ocs
        )

        if existing:
            # 캐시된 결과 반환
            logger.info(f'MG 캐시 결과 반환: ocs_id={ocs_id}, job_id={existing.job_id}')
            return Response({
                'job_id': existing.job_id,
                'status': 'completed',
                'cached': True,
                'message': '기존 추론 결과를 반환합니다.',
                'result': existing.result_data
            })

        # 5. 새 추론 생성
        inference = AIInference.objects.create(
            model_type=AIInference.ModelType.MG,
            patient=ocs.patient,
            rna_ocs=ocs,
            mode=mode,
            requested_by=request.user if request.user.is_authenticated else None,
            status=AIInference.Status.PENDING
        )

        # 6. CSV 파일 읽기 및 FastAPI 호출
        try:
            # CSV 파일 내용 읽기 (FastAPI에 내용 전달)
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_content = f.read()

            callback_url = request.build_absolute_uri('/api/ai/callback/')

            response = httpx.post(
                f"{FASTAPI_URL}/api/v1/mg/inference",
                json={
                    'job_id': inference.job_id,
                    'ocs_id': ocs_id,
                    'patient_id': ocs.patient.patient_number,
                    'csv_content': csv_content,  # 파일 경로 대신 내용 전송
                    'callback_url': callback_url,
                    'mode': mode,
                },
                timeout=30.0
            )
            response.raise_for_status()

            # 상태 업데이트
            inference.status = AIInference.Status.PROCESSING
            inference.save()

            return Response({
                'job_id': inference.job_id,
                'status': 'processing',
                'cached': False,
                'message': 'MG 추론이 시작되었습니다.'
            })

        except httpx.ConnectError:
            inference.status = AIInference.Status.FAILED
            inference.error_message = 'FastAPI 서버 연결 실패'
            inference.save()

            return Response(
                {'error': 'FastAPI 서버에 연결할 수 없습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except httpx.HTTPStatusError as e:
            inference.status = AIInference.Status.FAILED
            inference.error_message = str(e)
            inference.save()

            return Response(
                {'error': f'FastAPI 호출 실패: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InferenceCallbackView(APIView):
    """
    FastAPI 콜백 수신

    POST /api/ai/callback/
    - FastAPI에서 추론 결과와 파일 내용을 함께 전송
    - Django에서 CDSS_STORAGE/AI/<job_id>/에 파일 저장
    """
    permission_classes = [AllowAny]

    # CDSS_STORAGE 경로
    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def post(self, request):
        import base64
        import numpy as np

        job_id = request.data.get('job_id')
        cb_status = request.data.get('status')
        result_data = request.data.get('result_data', {})
        error_message = request.data.get('error_message')
        files_data = request.data.get('files', {})  # 파일 내용 (base64 인코딩)

        if not job_id:
            return Response(
                {'error': 'job_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 추론 조회
        try:
            inference = AIInference.objects.get(job_id=job_id)
        except AIInference.DoesNotExist:
            return Response(
                {'error': 'Job을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 상태 업데이트
        if cb_status == 'completed':
            # 파일 저장
            if files_data:
                saved_files = self._save_files(job_id, files_data)
                result_data['saved_files'] = saved_files
                logger.info(f'Files saved for job {job_id}: {list(saved_files.keys())}')

            inference.status = AIInference.Status.COMPLETED
            inference.result_data = result_data
            inference.completed_at = timezone.now()
        else:
            inference.status = AIInference.Status.FAILED
            inference.error_message = error_message

        inference.save()

        # WebSocket 알림 (manual 모드만)
        if inference.mode == AIInference.Mode.MANUAL:
            self._send_websocket_notification(inference)

        logger.info(f'Callback 처리 완료: job_id={job_id}, status={cb_status}')

        return Response({'status': 'ok'})

    def _save_files(self, job_id: str, files_data: dict) -> dict:
        """
        FastAPI에서 받은 파일 내용을 CDSS_STORAGE에 저장

        Args:
            job_id: 작업 ID
            files_data: {filename: {content: base64, type: 'json'|'npz'|'png'}}

        Returns:
            저장된 파일명 목록
        """
        import base64
        import json
        import numpy as np

        output_dir = self.STORAGE_BASE / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {'job_id': job_id}

        for filename, file_info in files_data.items():
            try:
                content = file_info.get('content')
                file_type = file_info.get('type', 'binary')
                file_path = output_dir / filename

                if file_type == 'json':
                    # JSON 파일은 문자열로 전송됨
                    if isinstance(content, str):
                        data = json.loads(content)
                    else:
                        data = content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                elif file_type == 'npz':
                    # NPZ 파일은 base64로 인코딩된 바이너리
                    binary_data = base64.b64decode(content)
                    with open(file_path, 'wb') as f:
                        f.write(binary_data)

                elif file_type == 'png':
                    # PNG 파일은 base64로 인코딩된 이미지
                    binary_data = base64.b64decode(content)
                    with open(file_path, 'wb') as f:
                        f.write(binary_data)

                else:
                    # 기타 바이너리 파일
                    binary_data = base64.b64decode(content)
                    with open(file_path, 'wb') as f:
                        f.write(binary_data)

                # 파일명에서 확장자 제거한 키 생성
                key = filename.rsplit('.', 1)[0] if '.' in filename else filename
                saved_files[key] = filename
                logger.info(f'  Saved: {filename}')

            except Exception as e:
                logger.error(f'Failed to save file {filename}: {e}')

        return saved_files

    def _send_websocket_notification(self, inference):
        """WebSocket으로 결과 알림"""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'ai_inference',
                {
                    'type': 'ai_inference_result',
                    'job_id': inference.job_id,
                    'model_type': inference.model_type,
                    'status': inference.status,
                    'result': inference.result_data if inference.status == AIInference.Status.COMPLETED else None,
                    'error': inference.error_message if inference.status == AIInference.Status.FAILED else None,
                }
            )
        except Exception as e:
            logger.error(f'WebSocket 알림 실패: {str(e)}')


class AIInferenceListView(APIView):
    """
    AI 추론 목록 조회

    GET /api/ai/inferences/
    - model_type: M1, MG, MM (선택)
    - status: PENDING, PROCESSING, COMPLETED, FAILED (선택)
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    def get(self, request):
        model_type = request.query_params.get('model_type')
        status_filter = request.query_params.get('status')

        queryset = AIInference.objects.select_related('patient', 'mri_ocs').all()

        if model_type:
            queryset = queryset.filter(model_type=model_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        queryset = queryset.order_by('-created_at')[:50]

        serializer = AIInferenceSerializer(queryset, many=True)
        return Response(serializer.data)


class AIInferenceDetailView(APIView):
    """
    AI 추론 상세 조회/삭제

    GET /api/ai/inferences/<job_id>/
    DELETE /api/ai/inferences/<job_id>/
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    # CDSS_STORAGE 경로
    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def get(self, request, job_id):
        try:
            inference = AIInference.objects.select_related('patient', 'mri_ocs').get(job_id=job_id)
        except AIInference.DoesNotExist:
            return Response(
                {'error': '추론 결과를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AIInferenceSerializer(inference)
        return Response(serializer.data)

    def delete(self, request, job_id):
        """추론 결과 삭제 (DB + 파일)"""
        import shutil
        import stat
        import os

        def remove_readonly(func, path, excinfo):
            """읽기 전용 파일 권한 변경 후 삭제"""
            os.chmod(path, stat.S_IWRITE)
            func(path)

        try:
            inference = AIInference.objects.get(job_id=job_id)
        except AIInference.DoesNotExist:
            return Response(
                {'error': '추론 결과를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 결과 파일 디렉토리 삭제
        result_dir = self.STORAGE_BASE / job_id
        if result_dir.exists():
            try:
                shutil.rmtree(result_dir, onerror=remove_readonly)
                logger.info(f'Deleted result directory: {result_dir}')
            except Exception as e:
                logger.error(f'Failed to delete result directory: {e}')
                # 실패 시 subprocess로 강제 삭제 시도
                try:
                    import subprocess
                    subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', str(result_dir)], check=True)
                    logger.info(f'Force deleted result directory: {result_dir}')
                except Exception as e2:
                    logger.error(f'Force delete also failed: {e2}')

        # DB 레코드 삭제
        inference.delete()
        logger.info(f'Deleted inference record: {job_id}')

        return Response({'message': f'추론 결과 {job_id}가 삭제되었습니다.'}, status=status.HTTP_200_OK)


class AIInferenceDeleteByOCSView(APIView):
    """
    OCS ID로 AI 추론 결과 삭제

    DELETE /api/ai/inferences/by-ocs/<ocs_id>/
    - 해당 OCS와 연결된 모든 추론 결과 삭제 (DB + 파일)
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def delete(self, request, ocs_id):
        """OCS ID로 추론 결과 삭제"""
        import shutil
        import stat
        import os
        import subprocess

        def remove_readonly(func, path, excinfo):
            """읽기 전용 파일 권한 변경 후 삭제"""
            os.chmod(path, stat.S_IWRITE)
            func(path)

        # OCS ID로 연결된 모든 추론 찾기
        inferences = AIInference.objects.filter(mri_ocs_id=ocs_id)

        if not inferences.exists():
            return Response(
                {'error': f'OCS ID {ocs_id}에 연결된 추론 결과가 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        deleted_jobs = []
        for inference in inferences:
            job_id = inference.job_id

            # 결과 파일 디렉토리 삭제
            result_dir = self.STORAGE_BASE / job_id
            if result_dir.exists():
                try:
                    shutil.rmtree(result_dir, onerror=remove_readonly)
                    logger.info(f'Deleted result directory: {result_dir}')
                except Exception as e:
                    logger.error(f'Failed to delete result directory {result_dir}: {e}')
                    # 실패 시 subprocess로 강제 삭제 시도
                    try:
                        subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', str(result_dir)], check=True)
                        logger.info(f'Force deleted result directory: {result_dir}')
                    except Exception as e2:
                        logger.error(f'Force delete also failed: {e2}')

            deleted_jobs.append(job_id)

        # DB 레코드 일괄 삭제
        count = inferences.count()
        inferences.delete()
        logger.info(f'Deleted {count} inference records for OCS ID {ocs_id}')

        return Response({
            'message': f'OCS ID {ocs_id}의 추론 결과 {count}건이 삭제되었습니다.',
            'deleted_jobs': deleted_jobs
        }, status=status.HTTP_200_OK)


class AIInferenceFileDownloadView(APIView):
    """
    AI 추론 결과 파일 다운로드

    GET /api/ai/inferences/<job_id>/files/<filename>/
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    # CDSS_STORAGE 경로 (modAI에서 저장하는 위치)
    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def get(self, request, job_id, filename):
        try:
            inference = AIInference.objects.get(job_id=job_id)
        except AIInference.DoesNotExist:
            raise Http404('추론 결과를 찾을 수 없습니다.')

        # 결과 디렉토리
        result_dir = self.STORAGE_BASE / job_id
        file_path = result_dir / filename

        # 보안: 경로 탈출 방지
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(self.STORAGE_BASE.resolve())):
                raise Http404('잘못된 경로입니다.')
        except Exception:
            raise Http404('잘못된 경로입니다.')

        if not file_path.exists():
            raise Http404('파일을 찾을 수 없습니다.')

        # MIME 타입 결정
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'

        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class AIInferenceFilesListView(APIView):
    """
    AI 추론 결과 파일 목록 조회

    GET /api/ai/inferences/<job_id>/files/
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def get(self, request, job_id):
        try:
            inference = AIInference.objects.get(job_id=job_id)
        except AIInference.DoesNotExist:
            return Response(
                {'error': '추론 결과를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        result_dir = self.STORAGE_BASE / job_id
        files = []

        if result_dir.exists():
            for file_path in result_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        'name': file_path.name,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'download_url': f'/api/ai/inferences/{job_id}/files/{file_path.name}/'
                    })

        return Response({
            'job_id': job_id,
            'status': inference.status,
            'files': files
        })


class AIInferenceSegmentationView(APIView):
    """
    AI 추론 세그멘테이션 데이터 조회 (SegMRIViewer용)

    GET /api/ai/inferences/<job_id>/segmentation/
    GET /api/ai/inferences/<job_id>/segmentation/?enc=binary  (최적화된 바이너리 포맷)

    Returns:
        - mri: 3D MRI 볼륨 (T1CE) - base64 인코딩 또는 리스트
        - prediction: 3D 세그멘테이션 마스크 - base64 인코딩 또는 리스트
        - shape: 볼륨 크기 [X, Y, Z]
        - volumes: 종양 볼륨 정보
        - encoding: 'base64' 또는 'list'
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")

    def _encode_array(self, arr, use_binary=True):
        """numpy array를 base64 또는 list로 인코딩"""
        import base64
        import numpy as np

        if use_binary:
            # float32로 변환 후 base64 인코딩 (훨씬 빠름)
            arr_f32 = arr.astype(np.float32)
            return base64.b64encode(arr_f32.tobytes()).decode('ascii')
        else:
            return arr.tolist()

    def get(self, request, job_id):
        import numpy as np
        import time

        start_time = time.time()

        # enc=binary 파라미터로 바이너리 모드 활성화 (기본값: True)
        use_binary = request.query_params.get('enc', 'binary') == 'binary'

        try:
            inference = AIInference.objects.get(job_id=job_id)
        except AIInference.DoesNotExist:
            return Response(
                {'error': '추론 결과를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        result_dir = self.STORAGE_BASE / job_id
        seg_file = result_dir / "m1_segmentation.npz"
        mri_file = result_dir / "m1_preprocessed_mri.npz"

        if not seg_file.exists():
            return Response(
                {'error': '세그멘테이션 파일을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # 세그멘테이션 NPZ 파일 로드
            seg_data = np.load(seg_file, allow_pickle=True)

            # 세그멘테이션 마스크 (mask 또는 segmentation_mask 키 사용)
            if 'mask' in seg_data:
                seg_mask = seg_data['mask']  # (128, 128, 128)
            elif 'segmentation_mask' in seg_data:
                seg_mask = seg_data['segmentation_mask']
            else:
                raise KeyError(f"세그멘테이션 키를 찾을 수 없습니다. 가능한 키: {list(seg_data.keys())}")

            # 볼륨 정보
            volumes = {}
            for key in ['wt_volume', 'tc_volume', 'et_volume', 'ncr_volume', 'ed_volume']:
                if key in seg_data:
                    vol_val = seg_data[key]
                    volumes[key] = float(vol_val.item()) if hasattr(vol_val, 'item') else float(vol_val)

            # 전처리된 MRI NPZ 파일 로드 (4채널: T1, T1CE, T2, FLAIR)
            mri_channels = {}
            mri_data = None

            if mri_file.exists():
                mri_npz = np.load(mri_file, allow_pickle=True)
                logger.info(f'Preprocessed MRI file found: {list(mri_npz.keys())}')

                # 4채널 MRI 데이터 로드
                for ch_name in ['t1', 't1ce', 't2', 'flair']:
                    if ch_name in mri_npz:
                        mri_channels[ch_name] = self._encode_array(mri_npz[ch_name], use_binary)

                # 기본 표시용 MRI는 T1CE 채널 사용
                if 't1ce' in mri_npz:
                    mri_data = mri_npz['t1ce']
                elif 't1' in mri_npz:
                    mri_data = mri_npz['t1']

                logger.info(f'MRI channels loaded: {list(mri_channels.keys())}')
            else:
                # 이전 버전 호환: segmentation.npz에서 MRI 찾기
                if 'mri' in seg_data:
                    mri_data = seg_data['mri']
                    logger.info(f'MRI data found in segmentation NPZ (legacy)')

            # 응답 데이터 구성
            response_data = {
                'job_id': job_id,
                'shape': list(seg_mask.shape),
                'prediction': self._encode_array(seg_mask, use_binary),
                'volumes': volumes,
                'encoding': 'base64' if use_binary else 'list',
                'dtype': 'float32',
            }

            # MRI 데이터 (기본: T1CE)
            if mri_data is not None:
                response_data['mri'] = self._encode_array(mri_data, use_binary)
            else:
                # MRI가 없으면 빈 배열
                empty_arr = np.zeros(seg_mask.shape, dtype=np.float32)
                response_data['mri'] = self._encode_array(empty_arr, use_binary)

            # 4채널 MRI 데이터 (새로운 추론 결과에만 있음)
            if mri_channels:
                response_data['mri_channels'] = mri_channels

            # Ground Truth 데이터 (있는 경우)
            if 'ground_truth' in seg_data:
                gt_mask = seg_data['ground_truth']
                response_data['groundTruth'] = self._encode_array(gt_mask, use_binary)
                response_data['has_ground_truth'] = True

                # GT 볼륨 정보 추가
                gt_volumes = {}
                for key in ['gt_wt_volume', 'gt_tc_volume', 'gt_et_volume', 'gt_ncr_volume', 'gt_ed_volume']:
                    if key in seg_data:
                        vol_val = seg_data[key]
                        gt_volumes[key] = float(vol_val.item()) if hasattr(vol_val, 'item') else float(vol_val)
                if gt_volumes:
                    response_data['gt_volumes'] = gt_volumes

                logger.info(f'Ground Truth loaded: shape={gt_mask.shape}')
            else:
                # Ground Truth가 없으면 Prediction을 GT로 사용 (기존 동작 유지)
                response_data['groundTruth'] = response_data['prediction']
                response_data['has_ground_truth'] = False
                logger.info('No Ground Truth found, using prediction as GT')

            elapsed = time.time() - start_time
            logger.info(f'Segmentation data prepared in {elapsed:.2f}s (binary={use_binary}, has_gt={response_data["has_ground_truth"]})')

            return Response(response_data)

        except Exception as e:
            logger.error(f'세그멘테이션 데이터 로드 실패: {str(e)}')
            return Response(
                {'error': f'데이터 로드 실패: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MGGeneExpressionView(APIView):
    """
    MG Gene Expression 분석 데이터 조회

    GET /api/ai/mg/gene-expression/<ocs_id>/
    - ocs_id를 기반으로 gene_expression.csv를 읽고 분석 데이터 반환
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    STORAGE_BASE = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE")

    def get(self, request, ocs_id):
        import math

        # 1. OCS 조회
        try:
            ocs = OCS.objects.get(id=ocs_id)
        except OCS.DoesNotExist:
            return Response(
                {'error': 'OCS를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 2. LIS 타입 검증
        if ocs.job_role != 'LIS':
            return Response(
                {'error': 'MG Gene Expression은 LIS OCS에서만 가능합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. CSV 파일 경로 찾기
        worker_result = ocs.worker_result or {}
        files = worker_result.get('files', [])

        if not files:
            return Response(
                {'error': 'Gene Expression CSV 파일이 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        csv_filename = files[0].get('name')
        if not csv_filename:
            return Response(
                {'error': 'CSV 파일명을 찾을 수 없습니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        folder_name = ocs.ocs_id.upper()
        csv_path = self.STORAGE_BASE / "LIS" / folder_name / csv_filename

        if not csv_path.exists():
            return Response(
                {'error': f'CSV 파일을 찾을 수 없습니다: {csv_path}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. CSV 파싱 및 분석
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()

            gene_data = self._parse_csv(content)

            if not gene_data or len(gene_data['values']) == 0:
                return Response(
                    {'error': 'CSV 파싱 실패 또는 데이터 없음'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5. 전처리 및 통계 계산
            preprocessed = self._preprocess_values(gene_data['values'])
            stats = self._calculate_stats(preprocessed)
            distribution = self._calculate_distribution(preprocessed, stats)
            top_genes = self._get_top_genes(gene_data['genes'], gene_data['values'], preprocessed, stats)

            return Response({
                'ocs_id': ocs_id,
                'patient_id': ocs.patient.patient_number if ocs.patient else None,
                'gene_count': len(gene_data['values']),
                'stats': stats,
                'distribution': distribution,
                'topGenes': top_genes,
            })

        except Exception as e:
            logger.error(f'Gene Expression 분석 실패: {str(e)}')
            return Response(
                {'error': f'분석 실패: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_csv(self, content: str) -> dict:
        """CSV 파싱 (Wide/Long format 지원)"""
        lines = content.strip().split('\n')
        if len(lines) < 2:
            return {'genes': [], 'values': []}

        header = [h.strip().lower() for h in lines[0].split(',')]

        # Wide format 감지
        if header[0] in ['patient_id', 'sample', 'id', 'sample_id']:
            return self._parse_wide_format(lines)

        # Long format (Gene, Value)
        genes = []
        values = []

        for i in range(1, len(lines)):
            parts = lines[i].split(',')
            if len(parts) >= 2:
                genes.append(parts[0].strip())
                try:
                    values.append(float(parts[1].strip()))
                except ValueError:
                    values.append(0.0)

        return {'genes': genes, 'values': values}

    def _parse_wide_format(self, lines: list) -> dict:
        """Wide format CSV 파싱 (첫 번째 환자 데이터 사용)"""
        header = [h.strip() for h in lines[0].split(',')]
        genes = header[1:]  # 첫 열은 Patient ID

        if len(lines) < 2:
            return {'genes': genes, 'values': [0.0] * len(genes)}

        parts = lines[1].split(',')
        values = []
        for v in parts[1:]:
            try:
                values.append(float(v.strip()))
            except ValueError:
                values.append(0.0)

        return {'genes': genes, 'values': values}

    def _preprocess_values(self, values: list) -> list:
        """log2(x+1) + z-score 전처리"""
        import math

        # log2(x+1) 변환
        log_values = [math.log2(v + 1) if v >= 0 else 0 for v in values]

        # z-score 정규화
        n = len(log_values)
        if n == 0:
            return []

        mean = sum(log_values) / n
        variance = sum((v - mean) ** 2 for v in log_values) / n
        std = math.sqrt(variance) if variance > 0 else 1

        if std > 0:
            return [(v - mean) / std for v in log_values]
        return log_values

    def _calculate_stats(self, values: list) -> dict:
        """통계 계산"""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            'count': n,
            'mean': sum(values) / n,
            'std': (sum((v - sum(values) / n) ** 2 for v in values) / n) ** 0.5,
            'median': sorted_values[n // 2],
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'q1': sorted_values[int(n * 0.25)],
            'q3': sorted_values[int(n * 0.75)],
        }

    def _calculate_distribution(self, values: list, stats: dict) -> list:
        """히스토그램 분포 계산"""
        if not values or not stats:
            return []

        min_val = stats['min']
        max_val = stats['max']
        bin_count = 10
        bin_size = (max_val - min_val) / bin_count if max_val > min_val else 1

        bins = [0] * bin_count
        for v in values:
            bin_idx = min(int((v - min_val) / bin_size), bin_count - 1)
            bins[bin_idx] += 1

        max_bin = max(bins) if bins else 1

        return [
            {
                'range': f"{(min_val + i * bin_size):.1f}~{(min_val + (i + 1) * bin_size):.1f}",
                'count': count,
                'percent': (count / max_bin) * 100 if max_bin > 0 else 0
            }
            for i, count in enumerate(bins)
        ]

    def _get_top_genes(self, genes: list, raw_values: list, preprocessed: list, stats: dict) -> list:
        """Top 10 발현 유전자"""
        if not genes or not preprocessed:
            return []

        indexed = [
            {'gene': genes[i], 'value': preprocessed[i], 'rawValue': raw_values[i]}
            for i in range(min(len(genes), len(preprocessed)))
        ]

        # z-score 기준 상위 10개
        indexed.sort(key=lambda x: x['value'], reverse=True)
        return indexed[:10]


# ============================================================
# MM (Multimodal) Inference Views
# ============================================================

class MMInferenceView(APIView):
    """
    MM 추론 요청 (Multimodal: MRI + Gene + Protein)

    POST /api/ai/mm/inference/
    - mri_ocs_id: MRI OCS ID (M1 추론 완료된 것)
    - gene_ocs_id: RNA_SEQ OCS ID (MG 추론 완료된 것)
    - protein_ocs_id: PROTEIN OCS ID
    - mode: 'manual' | 'auto'

    각 OCS에서 필요한 feature 파일을 읽어서 FastAPI에 전송
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    # CDSS_STORAGE 경로
    STORAGE_AI = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/AI")
    STORAGE_LIS = Path("C:/Users/401-24/Desktop/ml-server-final/source/CDSS_STORAGE/LIS")

    def post(self, request):
        import numpy as np
        import json

        mri_ocs_id = request.data.get('mri_ocs_id')
        gene_ocs_id = request.data.get('gene_ocs_id')
        protein_ocs_id = request.data.get('protein_ocs_id')
        mode = request.data.get('mode', 'manual')

        # 1. 최소 하나의 모달리티 필수
        if not any([mri_ocs_id, gene_ocs_id, protein_ocs_id]):
            return Response(
                {'error': '최소 하나의 OCS ID가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 환자 확인 (첫 번째 유효한 OCS에서)
        patient = None
        base_ocs = None

        for ocs_id in [mri_ocs_id, gene_ocs_id, protein_ocs_id]:
            if ocs_id:
                try:
                    ocs = OCS.objects.select_related('patient').get(id=ocs_id)
                    if patient is None:
                        patient = ocs.patient
                        base_ocs = ocs
                    elif patient.id != ocs.patient_id:
                        return Response(
                            {'error': '모든 OCS는 동일한 환자여야 합니다.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except OCS.DoesNotExist:
                    return Response(
                        {'error': f'OCS {ocs_id}를 찾을 수 없습니다.'},
                        status=status.HTTP_404_NOT_FOUND
                    )

        # 3. Feature 데이터 로드
        mri_features = None
        gene_features = None
        protein_data = None
        mri_ocs = None
        gene_ocs = None
        protein_ocs = None

        # 3.1 MRI Features (m1_encoder_features.npz)
        if mri_ocs_id:
            mri_ocs = OCS.objects.get(id=mri_ocs_id)
            # M1 추론 완료된 job_id 찾기
            m1_inference = AIInference.objects.filter(
                model_type=AIInference.ModelType.M1,
                mri_ocs_id=mri_ocs_id,
                status=AIInference.Status.COMPLETED
            ).order_by('-completed_at').first()

            if not m1_inference:
                return Response(
                    {'error': f'MRI OCS {mri_ocs_id}에 대한 M1 추론 결과가 없습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # m1_encoder_features.npz 읽기
            features_path = self.STORAGE_AI / m1_inference.job_id / 'm1_encoder_features.npz'
            if not features_path.exists():
                return Response(
                    {'error': f'M1 encoder features 파일을 찾을 수 없습니다: {features_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                npz_data = np.load(str(features_path))
                mri_features = npz_data['features'].tolist()  # m1_service.py에서 'features' 키로 저장됨
                logger.info(f'[MM] Loaded MRI features: {len(mri_features)}-dim from {features_path}')
            except Exception as e:
                return Response(
                    {'error': f'M1 encoder features 로드 실패: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # 3.2 Gene Features (mg_gene_features.json)
        if gene_ocs_id:
            gene_ocs = OCS.objects.get(id=gene_ocs_id)
            # MG 추론 완료된 job_id 찾기
            mg_inference = AIInference.objects.filter(
                model_type=AIInference.ModelType.MG,
                rna_ocs_id=gene_ocs_id,
                status=AIInference.Status.COMPLETED
            ).order_by('-completed_at').first()

            if not mg_inference:
                return Response(
                    {'error': f'RNA_SEQ OCS {gene_ocs_id}에 대한 MG 추론 결과가 없습니다.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # mg_gene_features.json 읽기
            features_path = self.STORAGE_AI / mg_inference.job_id / 'mg_gene_features.json'
            if not features_path.exists():
                return Response(
                    {'error': f'MG gene features 파일을 찾을 수 없습니다: {features_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                with open(features_path, 'r', encoding='utf-8') as f:
                    features_data = json.load(f)
                gene_features = features_data.get('features', [])
                logger.info(f'[MM] Loaded Gene features: {len(gene_features)}-dim from {features_path}')
            except Exception as e:
                return Response(
                    {'error': f'MG gene features 로드 실패: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # 3.3 Protein Data (rppa.csv from CDSS_STORAGE/LIS/<ocs_id>/)
        if protein_ocs_id:
            protein_ocs = OCS.objects.get(id=protein_ocs_id)
            # rppa.csv 파일 읽기 (ocs_id 필드값 사용: ocs_0045 형식)
            rppa_path = self.STORAGE_LIS / protein_ocs.ocs_id / 'rppa.csv'
            if not rppa_path.exists():
                return Response(
                    {'error': f'RPPA 파일을 찾을 수 없습니다: {rppa_path}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                with open(rppa_path, 'r', encoding='utf-8') as f:
                    protein_data = f.read()
                logger.info(f'[MM] Loaded Protein data: {len(protein_data)} chars from {rppa_path}')
            except Exception as e:
                return Response(
                    {'error': f'RPPA 파일 로드 실패: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # 4. 기존 완료된 추론 확인
        existing = AIInference.find_existing(
            model_type=AIInference.ModelType.MM,
            mri_ocs=mri_ocs,
            rna_ocs=gene_ocs,
            protein_ocs=protein_ocs
        )

        if existing:
            logger.info(f'[MM] 캐시 결과 반환: job_id={existing.job_id}')
            return Response({
                'job_id': existing.job_id,
                'status': 'completed',
                'cached': True,
                'message': '기존 추론 결과를 반환합니다.',
                'result': existing.result_data
            })

        # 5. 새 추론 생성
        inference = AIInference.objects.create(
            model_type=AIInference.ModelType.MM,
            patient=patient,
            mri_ocs=mri_ocs,
            rna_ocs=gene_ocs,
            protein_ocs=protein_ocs,
            mode=mode,
            requested_by=request.user if request.user.is_authenticated else None,
            status=AIInference.Status.PENDING
        )

        # 6. FastAPI 호출
        try:
            callback_url = request.build_absolute_uri('/api/ai/callback/')

            response = httpx.post(
                f"{FASTAPI_URL}/api/v1/mm/inference",
                json={
                    'job_id': inference.job_id,
                    'ocs_id': protein_ocs_id or gene_ocs_id or mri_ocs_id,  # 기준 OCS
                    'patient_id': patient.patient_number,
                    'mri_features': mri_features,
                    'gene_features': gene_features,
                    'protein_data': protein_data,
                    'mri_ocs_id': mri_ocs_id,
                    'gene_ocs_id': gene_ocs_id,
                    'protein_ocs_id': protein_ocs_id,
                    'callback_url': callback_url,
                    'mode': mode,
                },
                timeout=60.0  # Feature 데이터가 크므로 타임아웃 증가
            )
            response.raise_for_status()

            # 상태 업데이트
            inference.status = AIInference.Status.PROCESSING
            inference.save()

            return Response({
                'job_id': inference.job_id,
                'status': 'processing',
                'cached': False,
                'message': 'MM 추론이 시작되었습니다.',
                'modalities': {
                    'mri': mri_features is not None,
                    'gene': gene_features is not None,
                    'protein': protein_data is not None,
                }
            })

        except httpx.ConnectError:
            inference.status = AIInference.Status.FAILED
            inference.error_message = 'FastAPI 서버 연결 실패'
            inference.save()

            return Response(
                {'error': 'FastAPI 서버에 연결할 수 없습니다.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        except httpx.HTTPStatusError as e:
            inference.status = AIInference.Status.FAILED
            inference.error_message = str(e)
            inference.save()

            return Response(
                {'error': f'FastAPI 호출 실패: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MMAvailableOCSView(APIView):
    """
    MM 추론에 사용 가능한 OCS 목록 조회

    GET /api/ai/mm/available-ocs/<patient_id>/
    - MRI OCS: M1 추론 완료 + OCS 상태 CONFIRMED
    - RNA_SEQ OCS: MG 추론 완료 + OCS 상태 CONFIRMED
    - PROTEIN OCS: OCS 상태 CONFIRMED
    """
    permission_classes = [AllowAny]  # TODO: 개발용

    def get(self, request, patient_id):
        from apps.patients.models import Patient

        # 환자 조회
        try:
            patient = Patient.objects.get(patient_number=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {'error': '환자를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 1. MRI OCS (M1 추론 완료 + OCS CONFIRMED)
        m1_completed = AIInference.objects.filter(
            patient=patient,
            model_type=AIInference.ModelType.M1,
            status=AIInference.Status.COMPLETED
        ).select_related('mri_ocs').order_by('-completed_at')

        mri_ocs_list = []
        seen_mri = set()
        for inf in m1_completed:
            if inf.mri_ocs and inf.mri_ocs.id not in seen_mri:
                # OCS 상태가 CONFIRMED인 것만
                if inf.mri_ocs.ocs_status == OCS.OcsStatus.CONFIRMED:
                    seen_mri.add(inf.mri_ocs.id)
                    mri_ocs_list.append({
                        'ocs_id': inf.mri_ocs.id,
                        'ocs_number': inf.mri_ocs.ocs_id,
                        'job_role': inf.mri_ocs.job_role,
                        'job_type': inf.mri_ocs.job_type,
                        'job_date': inf.mri_ocs.created_at.isoformat() if inf.mri_ocs.created_at else None,
                        'inference_job_id': inf.job_id,
                    })

        # 2. RNA_SEQ OCS (MG 추론 완료 + OCS CONFIRMED)
        mg_completed = AIInference.objects.filter(
            patient=patient,
            model_type=AIInference.ModelType.MG,
            status=AIInference.Status.COMPLETED
        ).select_related('rna_ocs').order_by('-completed_at')

        rna_ocs_list = []
        seen_rna = set()
        for inf in mg_completed:
            if inf.rna_ocs and inf.rna_ocs.id not in seen_rna:
                # OCS 상태가 CONFIRMED인 것만
                if inf.rna_ocs.ocs_status == OCS.OcsStatus.CONFIRMED:
                    seen_rna.add(inf.rna_ocs.id)
                    rna_ocs_list.append({
                        'ocs_id': inf.rna_ocs.id,
                        'ocs_number': inf.rna_ocs.ocs_id,
                        'job_role': inf.rna_ocs.job_role,
                        'job_type': inf.rna_ocs.job_type,
                        'job_date': inf.rna_ocs.created_at.isoformat() if inf.rna_ocs.created_at else None,
                        'inference_job_id': inf.job_id,
                    })

        # 3. PROTEIN OCS (OCS CONFIRMED만)
        protein_ocs_queryset = OCS.objects.filter(
            patient=patient,
            job_type='PROTEIN',
            ocs_status=OCS.OcsStatus.CONFIRMED
        ).order_by('-created_at')

        protein_ocs_list = []
        for ocs in protein_ocs_queryset:
            protein_ocs_list.append({
                'ocs_id': ocs.id,
                'ocs_number': ocs.ocs_id,
                'job_role': ocs.job_role,
                'job_type': ocs.job_type,
                'job_date': ocs.created_at.isoformat() if ocs.created_at else None,
            })

        return Response({
            'patient_id': patient_id,
            'patient_name': patient.name,
            'mri_ocs': mri_ocs_list,
            'rna_ocs': rna_ocs_list,
            'protein_ocs': protein_ocs_list,
        })

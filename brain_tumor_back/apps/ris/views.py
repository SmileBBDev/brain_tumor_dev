
from rest_framework import viewsets, status, views, parsers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.http import HttpResponse, StreamingHttpResponse
import requests
import mimetypes
import logging
from rest_framework.renderers import JSONRenderer, BaseRenderer, BrowsableAPIRenderer
from rest_framework.decorators import renderer_classes

logger = logging.getLogger(__name__)

class DicomJsonRenderer(BaseRenderer):
    media_type = 'application/dicom+json'
    format = 'dicomjson'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

from .models import RadiologyOrder, RadiologyStudy, RadiologyReport
from .serializers import RadiologyOrderSerializer, RadiologyStudySerializer, RadiologyReportSerializer
from .services import RadiologyOrderService, RadiologyStudyService, RadiologyReportService
from .clients.orthanc_client import OrthancClient


@extend_schema(
    summary="Orthanc 상태 확인",
    responses={200: OpenApiTypes.OBJECT},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # 개발 모드
def orthanc_health_check(request):
    """Orthanc 서버 연결 상태 확인"""
    client = OrthancClient()
    result = client.health_check()
    return Response(result)


# --- OHIF Viewer & Orthanc Proxy ---

@extend_schema(
    summary="DICOM-Web 프록시 (X-Accel-Redirect)",
    description="Nginx의 internal endpoint로 리다이렉트하여 Orthanc가 직접 데이터를 서빙하도록 합니다.",
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.NONE},
    tags=['ris']
)
@api_view(['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@permission_classes([AllowAny]) # TODO: 배포 시 IsAuthenticated로 변경 권장
def dicom_web_proxy(request, path):
    """
    Orthanc DICOM-Web API 프록시 (Nginx X-Accel-Redirect)
    
    Django는 인증/인가만 수행하고, 실제 데이터 전송은 Nginx가 담당합니다.
    """
    # 1. Nginx 내부 리다이렉트 경로 설정 (dicom-web prefix 포함 확인 필요)
    # nginx.conf: location /internal-orthanc/ { proxy_pass http://orthanc_internal/; }
    # Target: http://orthanc_internal/dicom-web/{path}
    
    redirect_url = f"/internal-orthanc/dicom-web/{path}"
    
    # 2. Query Parameter 보존
    if request.query_params:
        redirect_url += f"?{request.GET.urlencode()}"

    response = HttpResponse()
    
    # 3. X-Accel-Redirect 헤더 설정
    response['X-Accel-Redirect'] = redirect_url
    
    # 4. Content-Type 및 기타 헤더 설정 (필요 시)
    # Nginx가 upstream의 헤더를 전달하므로 여기서는 최소한만 설정하거나 생략 가능
    # 단, 로깅을 위해 명시적으로 남길 수 있음
    logger.info(f"X-Accel-Redirect to: {redirect_url}")
    
    return response


@extend_schema(
    summary="OHIF Viewer 프록시",
    description="OHIF Viewer의 정적 파일 및 인덱스 페이지를 제공합니다.",
    responses={200: OpenApiTypes.NONE},
    tags=['ris'],
    operation_id="ris_viewer_proxy_path"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def ohif_viewer_proxy(request, path=''):
    """OHIF Viewer 정적 파일 프록시"""
    # path가 없으면 index.html 요청
    if not path:
        path = 'index.html'
        
    # Nginx가 /pacs-viewer/ 경로에서 정적 파일을 서빙하므로 리다이렉트 가능
    # 다만, API를 통해 접근해야 하는 경우 X-Accel-Redirect 사용
    
    # Nginx location /pacs-viewer/ -> alias /var/www/ohif-dist/
    # X-Accel mapping을 위해 별도 internal location이 없다면 직접 forward하거나
    # 클라이언트가 /pacs-viewer/를 직접 호출하도록 유도해야 함.
    # 현재 구조상 API에서 서빙하려면 StreamingHttpResponse 유지
    
    target_url = f"{settings.OHIF_VIEWER_URL}/{path}"
    
    try:
        response = requests.get(target_url, stream=True, timeout=10)
        content_type = response.headers.get('Content-Type')
        
        if path.endswith('.mjs'):
            content_type = 'application/javascript'
        elif not content_type:
            content_type, _ = mimetypes.guess_type(path)

        return StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=8192),
            status=response.status_code,
            content_type=content_type
        )
    except Exception as e:
        logger.error(f"OHIF Viewer proxy failed: {str(e)}", exc_info=True)
        return Response({"error": f"Viewer proxy failed: {str(e)}"}, status=500)


@extend_schema(
    summary="Nginx용 인증 확인 엔드포인트",
    description="Nginx의 auth_request 모듈에서 호출하며, 유효한 JWT 토큰이 있으면 200 OK를 반환합니다.",
    responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auth_check(request):
    """Nginx auth_request 전용 인증 확인"""
    return Response({
        "status": "authenticated",
        "user_id": str(request.user.user_id),
        "role": request.user.role
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary="OHIF Viewer 인덱스",
    responses={200: OpenApiTypes.NONE},
    tags=['ris'],
    operation_id="ris_viewer_index"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def ohif_viewer_index(request):
    """OHIF Viewer 메인 페이지 프록시"""
    return ohif_viewer_proxy(request, '')


@extend_schema(
    summary="WADO 프록시 (X-Accel-Redirect)",
    responses={200: OpenApiTypes.NONE},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def wado_proxy(request):
    """WADO-URI 프록시 (Nginx X-Accel-Redirect)"""
    # Target: /internal-orthanc/wado?requestType=WADO&...
    redirect_url = "/internal-orthanc/wado"
    
    if request.query_params:
        redirect_url += f"?{request.GET.urlencode()}"

    response = HttpResponse()
    response['X-Accel-Redirect'] = redirect_url
    logger.info(f"X-Accel-Redirect to: {redirect_url}")
    
    return response


@extend_schema(
    summary="Orthanc 환자 목록 테스트",
    responses={200: OpenApiTypes.OBJECT},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # 개발 모드
def test_orthanc_patients(request):
    """
    Orthanc 연동 테스트: 환자 목록 조회

    Orthanc에 저장된 모든 환자 데이터를 조회하여 Django에서 정상적으로
    통신할 수 있는지 확인합니다.

    Query Parameters:
        - page: 페이지 번호 (기본값: 1)
        - page_size: 페이지당 항목 수 (기본값: 10)
    """
    try:
        # 페이지네이션 파라미터 추출
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # 유효성 검증
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        client = OrthancClient()

        # Orthanc에서 환자 목록 조회
        patients_response = client.get('/patients')

        if not patients_response.get('success'):
            return Response({
                'success': False,
                'message': 'Orthanc 서버 연결 실패',
                'error': patients_response.get('error', 'Unknown error')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        patient_ids = patients_response.get('data', [])
        total_patients = len(patient_ids)

        # 페이지네이션 계산
        total_pages = (total_patients + page_size - 1) // page_size if total_patients > 0 else 1
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # 현재 페이지의 환자 ID 추출
        paginated_patient_ids = patient_ids[start_index:end_index]

        # 각 환자의 상세 정보 조회
        patients_detail = []
        for patient_id in paginated_patient_ids:
            patient_info = client.get(f'/patients/{patient_id}')
            if patient_info.get('success'):
                patient_data = patient_info.get('data', {})

                # MainDicomTags에서 환자 정보 추출
                main_tags = patient_data.get('MainDicomTags', {})

                patients_detail.append({
                    'patient_id': patient_id,
                    'patient_name': main_tags.get('PatientName', 'Unknown'),
                    'patient_birth_date': main_tags.get('PatientBirthDate', ''),
                    'patient_sex': main_tags.get('PatientSex', ''),
                    'studies': patient_data.get('Studies', []),
                    'study_count': len(patient_data.get('Studies', []))
                })

        return Response({
            'success': True,
            'message': 'Orthanc 연동 성공',
            'data': {
                'total_patients': total_patients,
                'current_page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'patients_detail_shown': len(patients_detail),
                'patients': patients_detail
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'Orthanc 조회 중 오류 발생',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Orthanc Study 목록 테스트",
    responses={200: OpenApiTypes.OBJECT},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([AllowAny])  # 개발 모드
def test_orthanc_studies(request):
    """
    Orthanc 연동 테스트: 검사(Study) 목록 조회

    Orthanc에 저장된 모든 검사 데이터를 조회합니다.

    Query Parameters:
        - page: 페이지 번호 (기본값: 1)
        - page_size: 페이지당 항목 수 (기본값: 10)
    """
    try:
        # 페이지네이션 파라미터 추출
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # 유효성 검증
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        client = OrthancClient()

        # Orthanc에서 Study 목록 조회
        studies_response = client.get('/studies')

        if not studies_response.get('success'):
            return Response({
                'success': False,
                'message': 'Orthanc 서버 연결 실패',
                'error': studies_response.get('error', 'Unknown error')
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        study_ids = studies_response.get('data', [])
        total_studies = len(study_ids)

        # 페이지네이션 계산
        total_pages = (total_studies + page_size - 1) // page_size if total_studies > 0 else 1
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        # 현재 페이지의 Study ID 추출
        paginated_study_ids = study_ids[start_index:end_index]

        # 각 Study의 상세 정보 조회
        studies_detail = []
        for study_id in paginated_study_ids:
            study_info = client.get(f'/studies/{study_id}')
            if study_info.get('success'):
                study_data = study_info.get('data', {})

                # MainDicomTags에서 검사 정보 추출
                main_tags = study_data.get('MainDicomTags', {})
                patient_tags = study_data.get('PatientMainDicomTags', {})

                studies_detail.append({
                    'study_id': study_id,
                    'study_instance_uid': main_tags.get('StudyInstanceUID', ''),
                    'study_date': main_tags.get('StudyDate', ''),
                    'study_time': main_tags.get('StudyTime', ''),
                    'study_description': main_tags.get('StudyDescription', ''),
                    'modality': main_tags.get('Modality', ''),
                    'patient_name': patient_tags.get('PatientName', 'Unknown'),
                    'patient_id': patient_tags.get('PatientID', ''),
                    'series': study_data.get('Series', []),
                    'series_count': len(study_data.get('Series', []))
                })

        return Response({
            'success': True,
            'message': 'Orthanc Study 조회 성공',
            'data': {
                'total_studies': total_studies,
                'current_page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_previous': page > 1,
                'studies_detail_shown': len(studies_detail),
                'studies': studies_detail
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': 'Orthanc Study 조회 중 오류 발생',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Orthanc Study 동기화",
    responses={200: OpenApiTypes.OBJECT},
    tags=['ris']
)
@api_view(['GET'])
@permission_classes([AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated])
def sync_orthanc_studies(request):
    """Orthanc에서 Study 목록을 가져와 Django DB에 동기화"""
    service = RadiologyStudyService()
    result = service.sync_studies_from_orthanc()

    return Response({
        'message': f"Synced {result['synced_count']} studies from Orthanc",
        'synced_count': result['synced_count'],
        'total': result['total']
    })


@extend_schema_view(
    list=extend_schema(
        summary="영상 검사 오더 목록 조회",
        description="모든 영상 검사 오더 목록을 조회합니다.",
        tags=["ris"]
    ),
    retrieve=extend_schema(
        summary="영상 검사 오더 상세 조회",
        description="특정 영상 검사 오더의 상세 정보를 조회합니다.",
        tags=["ris"]
    ),
    create=extend_schema(
        summary="영상 검사 오더 생성",
        description="새로운 영상 검사 오더를 생성합니다. Service 레이어를 통해 비즈니스 로직을 처리합니다.",
        tags=["ris"]
    ),
    update=extend_schema(
        summary="영상 검사 오더 수정",
        description="영상 검사 오더 정보를 수정합니다.",
        tags=["ris"]
    ),
    partial_update=extend_schema(
        summary="영상 검사 오더 부분 수정",
        description="영상 검사 오더 정보를 부분적으로 수정합니다.",
        tags=["ris"]
    ),
    destroy=extend_schema(
        summary="영상 검사 오더 삭제",
        description="영상 검사 오더를 삭제합니다.",
        tags=["ris"]
    ),
)
class RadiologyOrderViewSet(viewsets.ModelViewSet):
    queryset = RadiologyOrder.objects.select_related('ordered_by').all()
    serializer_class = RadiologyOrderSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]

    def perform_create(self, serializer):
        # Service 레이어 사용
        user = self.request.user if self.request.user.is_authenticated else None
        RadiologyOrderService.create_order(serializer.validated_data, user)


@extend_schema_view(
    list=extend_schema(
        summary="영상 Study 목록 조회",
        description="Orthanc에서 동기화된 영상 Study 목록을 조회합니다.",
        tags=["ris"]
    ),
    retrieve=extend_schema(
        summary="영상 Study 상세 조회",
        description="특정 영상 Study의 상세 정보를 조회합니다.",
        tags=["ris"]
    ),
)
class RadiologyStudyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RadiologyStudy.objects.select_related('order', 'patient').all()
    serializer_class = RadiologyStudySerializer
    lookup_field = 'study_instance_uid'
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]

    def get_object(self):
        """
        Study Instance UID 또는 Orthanc Study ID(UUID) 둘 다 지원하도록 오버라이드.
        """
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]

        from django.db.models import Q
        from django.shortcuts import get_object_or_404

        # DICOM UID 또는 Orthanc ID로 검색
        obj = get_object_or_404(queryset, Q(study_instance_uid=lookup_value) | Q(orthanc_study_id=lookup_value))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        summary="영상 Study 검색",
        description="환자 이름 또는 환자 ID로 영상 Study를 검색합니다.",
        tags=["ris"],
        parameters=[
            OpenApiParameter(
                name="patient_name",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="환자 이름",
                required=False,
            ),
            OpenApiParameter(
                name="patient_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="환자 ID",
                required=False,
            ),
        ],
    )

    @action(detail=False, methods=['get'])
    def search(self, request):
        from django.db.models import Q # Import inside method to avoid clutter or move to top if preferred. I'll put it here for safety against replacement errors.
        """환자 이름 또는 ID로 Study 검색"""
        patient_name = request.query_params.get('patient_name')
        patient_id = request.query_params.get('patient_id')

        queryset = self.get_queryset()
        if patient_name:
            queryset = queryset.filter(patient_name__icontains=patient_name)
        if patient_id:
            queryset = queryset.filter(Q(patient_id=patient_id) | Q(patient__patient_id=patient_id))

        serializer = self.get_serializer(queryset[:20], many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="영상 판독 보고서 목록 조회",
        description="모든 영상 판독 보고서 목록을 조회합니다.",
        tags=["ris"]
    ),
    retrieve=extend_schema(
        summary="영상 판독 보고서 상세 조회",
        description="특정 영상 판독 보고서의 상세 정보를 조회합니다.",
        tags=["ris"]
    ),
    create=extend_schema(
        summary="영상 판독 보고서 작성",
        description="새로운 영상 판독 보고서를 작성합니다.",
        tags=["ris"]
    ),
    update=extend_schema(
        summary="영상 판독 보고서 수정",
        description="영상 판독 보고서를 수정합니다.",
        tags=["ris"]
    ),
    partial_update=extend_schema(
        summary="영상 판독 보고서 부분 수정",
        description="영상 판독 보고서를 부분적으로 수정합니다.",
        tags=["ris"]
    ),
    destroy=extend_schema(
        summary="영상 판독 보고서 삭제",
        description="영상 판독 보고서를 삭제합니다.",
        tags=["ris"]
    ),
)
class RadiologyReportViewSet(viewsets.ModelViewSet):
    queryset = RadiologyReport.objects.select_related('study', 'radiologist', 'signed_by').all()
    serializer_class = RadiologyReportSerializer
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(radiologist=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """판독문 서명"""
        report = self.get_object()

        if report.status == 'FINAL':
            return Response(
                {'error': 'Report already finalized'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Service 레이어 사용
        service = RadiologyReportService()
        user = request.user if request.user.is_authenticated else None
        report = service.sign_report(report.report_id, user)

        serializer = self.get_serializer(report)
        return Response(serializer.data)


@extend_schema(
    summary="DICOM 업로드 및 HTJ2K 변환",
    description="DICOM 파일을 업로드하면 자동으로 HTJ2K(또는 JPEG 2000 Lossless)로 변환하여 Orthanc에 저장합니다.",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary'
                }
            }
        }
    },
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    tags=['ris']
)
class DicomUploadView(views.APIView):
    parser_classes = [parsers.MultiPartParser]
    permission_classes = [AllowAny if not settings.ENABLE_SECURITY else IsAuthenticated]

    def post(self, request, format=None):
        if 'file' not in request.FILES:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES['file']
        
        # Save to temp file
        import tempfile
        import os
        from ris.utils.dicom_converter import HTJ2KConverter
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.dcm', delete=False) as tmp:
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
                
            # Convert
            try:
                converted_path = HTJ2KConverter.convert_file(tmp_path)
            except Exception as e:
                logger.error(f"HTJ2K Conversion failed: {e}")
                os.unlink(tmp_path)
                return Response({'error': f"Conversion failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Upload to Orthanc
            client = OrthancClient()
            with open(converted_path, 'rb') as f:
                resp = requests.post(
                    f"{client.base_url}/instances",
                    data=f.read(),
                    auth=client.auth
                )
                
            # Cleanup
            os.unlink(tmp_path)
            if os.path.exists(converted_path) and converted_path != tmp_path:
                os.unlink(converted_path)

            if resp.status_code == 200:
                orthanc_resp = resp.json()
                return Response({
                    'message': 'Uploaded and converted successfully',
                    'orthanc_response': orthanc_resp
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': 'Orthanc upload failed',
                    'orthanc_status': resp.status_code,
                    'orthanc_message': resp.text
                }, status=resp.status_code)

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                 os.unlink(tmp_path)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

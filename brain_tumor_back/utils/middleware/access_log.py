import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('access')

class AccessLogMiddleware(MiddlewareMixin):
    """모든 요청과 응답을 로깅하는 미들웨어"""
    
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        # 실행 시간 계산
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # 기본 로그 정보
        log_data = {
            'ip': request.META.get('REMOTE_ADDR'),
            'method': request.method,
            'path': request.get_full_path(),
            'status': response.status_code,
            'duration': f"{duration:.3f}s",
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
        }
        
        # 로그 기록
        message = f"{log_data['ip']} {log_data['user']} {log_data['method']} {log_data['path']} {log_data['status']} ({log_data['duration']})"
        
        if response.status_code >= 400:
            logger.warning(message)
        else:
            logger.info(message)
            
        return response

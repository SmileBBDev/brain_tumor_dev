from rest_framework import permissions


class AIInferenceResultPermission(permissions.BasePermission):
    """
    AI 추론 결과 권한

    읽기 (GET): 의사, RIS, LIS 모두 허용
    쓰기 (POST, PUT, PATCH): RIS만 허용

    M1(Seg), MG(Grade), MM(MGMT) 모든 AI 결과에 동일 적용
    """

    ADMIN_ROLES = ['SYSTEMMANAGER', 'ADMIN']
    READ_ALLOWED_ROLES = ['DOCTOR', 'RIS', 'LIS']
    WRITE_ALLOWED_ROLES = ['RIS']

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        role_code = user_role.code if user_role else None

        # 관리자는 전체 권한
        if role_code in self.ADMIN_ROLES:
            return True

        # 읽기 작업: 의사, RIS, LIS 허용
        if request.method in permissions.SAFE_METHODS:
            return role_code in self.READ_ALLOWED_ROLES

        # 쓰기 작업 (review 등): RIS만 허용
        return role_code in self.WRITE_ALLOWED_ROLES

    def has_object_permission(self, request, view, obj):
        user_role = getattr(request.user, 'role', None)
        role_code = user_role.code if user_role else None

        # 관리자는 전체 권한
        if role_code in self.ADMIN_ROLES:
            return True

        # 읽기 작업: 의사, RIS, LIS 허용
        if request.method in permissions.SAFE_METHODS:
            return role_code in self.READ_ALLOWED_ROLES

        # 쓰기 작업: RIS만 허용
        return role_code in self.WRITE_ALLOWED_ROLES


class AIInferenceRequestPermission(permissions.BasePermission):
    """
    AI 추론 요청 권한

    읽기 (GET): 의사, RIS, LIS 모두 허용
    생성 (POST): 의사, RIS 허용
    취소 (cancel): 요청자 본인 또는 관리자
    """

    ADMIN_ROLES = ['SYSTEMMANAGER', 'ADMIN']
    READ_ALLOWED_ROLES = ['DOCTOR', 'RIS', 'LIS']
    CREATE_ALLOWED_ROLES = ['DOCTOR', 'RIS']

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user_role = getattr(request.user, 'role', None)
        role_code = user_role.code if user_role else None

        # 관리자는 전체 권한
        if role_code in self.ADMIN_ROLES:
            return True

        # 읽기 작업
        if request.method in permissions.SAFE_METHODS:
            return role_code in self.READ_ALLOWED_ROLES

        # 생성 작업
        if view.action == 'create':
            return role_code in self.CREATE_ALLOWED_ROLES

        # validate 액션은 읽기 권한 있으면 허용
        if view.action == 'validate':
            return role_code in self.READ_ALLOWED_ROLES

        return True  # object-level에서 체크

    def has_object_permission(self, request, view, obj):
        user_role = getattr(request.user, 'role', None)
        role_code = user_role.code if user_role else None

        # 관리자는 전체 권한
        if role_code in self.ADMIN_ROLES:
            return True

        # 읽기 작업
        if request.method in permissions.SAFE_METHODS:
            return role_code in self.READ_ALLOWED_ROLES

        # 취소는 요청자 본인만
        if view.action == 'cancel':
            return obj.requested_by == request.user

        return False

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from django.utils import timezone
from apps.accounts.models.role import Role
from apps.accounts.models.role_permission import RolePermission
from apps.accounts.models.permission import Permission
from apps.accounts.models.user import User
from apps.common.pagination import UserPagination
from apps.common.utils import get_client_ip
from apps.audit.services import create_audit_log # # Audit Log 기록 유틸


from apps.menus.models import Menu
from apps.menus.serializers import MenuSerializer

from .serializers import LoginSerializer, MeSerializer, CustomTokenObtainPairSerializer, RoleSerializer

# JWT 토큰 발급 View
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(
            data = request.data,
            context = {"request": request},
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            
            # 로그인 성공 처리
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            # 로그인 성공 시 실패 횟수 & 잠금 해제
            user.failed_login_count = 0
            user.is_locked = False
            user.locked_at = None
            
            # 변경된 필드만 업데이트
            user.save(update_fields=[
                "last_login",
                "last_login_ip",
                "failed_login_count",
                "is_locked",
                "locked_at",
            ])

            refresh = RefreshToken.for_user(user)

            create_audit_log(request, "LOGIN_SUCCESS", user) 

            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "user": {
                        "id": user.id,
                        "login_id": user.login_id,
                        "must_change_password": user.must_change_password,
                    }
                },
                status=status.HTTP_200_OK,
            )
        # 로그인 잠금으로 인한 실패 처리
        login_locked = serializer.validated_data.get(
            "login_locked",
            False
        )

        # 잠금이 아닌 경우만 LOGIN_FAIL 기록
        if not login_locked:
            create_audit_log(request, "LOGIN_FAIL")

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 내 정보 조회 view
class MeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(
            MeSerializer(request.user).data
        )
 
 
# 로그인 성공시 last_login 갱신 커스텀 토큰 뷰
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            user = User.objects.get(login_id=request.data["login_id"])
            user.last_seen = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=["last_seen", "last_login_ip"])

        return response

# 비밀번호 변경 API
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password", "").strip()
        new_password = request.data.get("new_password", "").strip()

        if not user.check_password(old_password):
            return Response(
                {"message": "현재 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save()

        return Response({"message": "비밀번호 변경 완료"})

# 역할(Role) CRUD API
# | 기능    | HTTP               |
# | -----  | ------------------ |
# | 역할 목록 | GET /roles         |
# | 역할 생성 | POST /roles        |
# | 역할 수정 | PUT /roles/{id}    |
# | 역할 삭제 | DELETE /roles/{id} |

class RoleViewSet(ModelViewSet): # - ModelViewSet을 상속하면 기본적으로 CRUD 엔드포인트가 자동으로 제공
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    pagination_class = UserPagination

    # 역할 조회
    def get_queryset(self):
        qs = Role.objects.all()

        search = self.request.query_params.get("search")
        status_param = self.request.query_params.get("status")

        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        if status_param == "ACTIVE":
            qs = qs.filter(is_active=True)
        elif status_param == "INACTIVE":
            qs = qs.filter(is_active=False)

        return qs
    
    # 역할 생성시
    # code 대문자로 넘어오지 않은 경우 대비
    def perform_create(self, serializer):
        serializer.save(
            code=serializer.validated_data["code"].upper()
        )

    # 역할 수정 put 방식
    def update(self, request, *args, **kwargs):
        request.data.pop("code", None)
        kwargs["partial"] = True   # PUT도 안전하게    
        return super().update(request, *args, **kwargs)

    # 역할 수정 patch 방식
    def partial_update(self, request, *args, **kwargs):
        request.data.pop("code", None)
        return super().partial_update(request, *args, **kwargs)
    
    # 역할 삭제
    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        role.is_active = False
        role.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    # 역할 메뉴 권한 저장
    # @action(detail=True, methods=["put"], url_path="menus")
    # def set_permissions(self, request, pk=None):
    #     role = self.get_object()
    #     permission_ids = request.data.get("permission_ids", [])
    #     # permission_ids = request.data 

    #     # menus = Menu.objects.filter(id__in=permission_ids)

    #     # # role.permissions.set(menus) 
    #     # role.menus.set(menus)
    #     # role.save()

    #     # return Response(
    #     #     {"message": "권한이 성공적으로 저장되었습니다."},
    #     #     status=status.HTTP_200_OK
    #     # )

    #     # 기존 권한 삭제
    #     RolePermission.objects.filter(role=role).delete()

    #     # 새 권한 bulk 생성
    #     RolePermission.objects.bulk_create([
    #         RolePermission(role=role, permission_id=pid)
    #         for pid in permission_ids

    #     ])

    #     return Response(
    #         {"message": "권한이 성공적으로 저장되었습니다."},
    #         status=status.HTTP_200_OK
    #     )
    
    # 역할별 권한 메뉴 조회
    # 조회 (URL 반드시 분리)
    @action(detail=True, methods=["get"], url_path="menu-ids")
    def menu_ids(self, request, pk=None):
        role = self.get_object()

        menu_ids = RolePermission.objects.filter(
            role=role
        ).values_list("permission_id", flat=True)

        return Response(list(menu_ids))

    
    # 역할별 메뉴 수정
    @action(detail=True, methods=["put"], url_path="menus")
    def update_menus(self, request, pk=None):
        from apps.accounts.services.permission_service import notify_permission_changed

        role = self.get_object()
        menu_ids = request.data.get("permission_ids", [])  # 프론트에서 permission_ids로 보내지만 실제로는 menu_ids

        if not isinstance(menu_ids, list):
            return Response(
                {"detail": "permission_ids must be a list"},
                status=400
            )

        # RolePermission.permission은 Menu를 참조함
        valid_menus = Menu.objects.filter(id__in=menu_ids)

        RolePermission.objects.filter(role=role).delete()

        RolePermission.objects.bulk_create([
            RolePermission(
                role=role,
                permission=menu  # Menu 객체
            )
            for menu in valid_menus
        ])

        # 해당 역할을 가진 모든 사용자에게 권한 변경 알림
        users_with_role = User.objects.filter(role=role)
        for user in users_with_role:
            try:
                notify_permission_changed(user.id)
            except Exception:
                pass  # WebSocket 연결이 없는 사용자는 무시

        return Response({
            "saved_permission_ids": list(
                valid_menus.values_list("id", flat=True)
            )
        })

    # @action(detail=True, methods=["put"], url_path="menus")
    # def update_menus(self, request, pk=None):
    #     role = self.get_object()
    #     permission_ids = request.data.get("permission_ids", [])

    #     # # 🔥 실제 Permission 테이블에 존재하는 것만 필터
    #     # valid_permissions = Permission.objects.filter(id__in=permission_ids)

    #     # 기존 삭제
    #     RolePermission.objects.filter(role=role).delete()

    #     menus = Menu.objects.filter(id__in=permission_ids)

    #     # 다시 저장 (FK 안전)
    #     RolePermission.objects.bulk_create([
    #         RolePermission(
    #             role=role,
    #             permission=perm
    #         )
    #         for perm in menus
    #     ])

    #     return Response({
    #     "saved_permission_ids": list(
    #         valid_permissions.values_list("id", flat=True)
    #     )
    # })




# 메뉴 권한 관리 CRUD
class PermissionViewSet(ReadOnlyModelViewSet):
    """
    메뉴(권한) 조회 전용 ViewSet
    """
    queryset = Menu.objects.filter(is_active=True).order_by("order")
    serializer_class = MenuSerializer

    def list(self, request, *args, **kwargs):
        menus = self.get_queryset()
        menu_tree = self.build_tree(menus)
        return Response(menu_tree)

    def build_tree(self, menus):
        menu_dict = {}
        tree = []

        for menu in menus:
            menu_dict[menu.id] = {
                "id": menu.id,
                "code": menu.code,
                "breadcrumbOnly": menu.breadcrumb_only,
                "labels": {
                    label.role: label.text
                    for label in menu.labels.all()
                },
                "children": [],
            }

        for menu in menus:
            if menu.parent_id:
                menu_dict[menu.parent_id]["children"].append(
                    menu_dict[menu.id]
                )
            else:
                tree.append(menu_dict[menu.id])

        return tree


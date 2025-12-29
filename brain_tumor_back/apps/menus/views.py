from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import get_user_menus
from .utils import build_menu_tree
from .models import Menu
from .serializers import MenuSerializer


# 메뉴 API
class UserMenuView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user_role = getattr(request.user, "role", None)

        # 최상위 메뉴만 가져오기

        menus = get_user_menus(request.user)
        tree = build_menu_tree(menus)
        
        return Response({"menus": tree})
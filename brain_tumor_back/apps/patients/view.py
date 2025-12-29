# apps/patients/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Patient
from .serializers import PatientSerializer
from apps.authorization.permissions import HasPermission # 권한 check를 담은 로직

# 참고용(HasPermission 사용법)
class PatientListView(APIView):
    permission_classes = [HasPermission]
    required_permission = "VIEW_PATIENT"

    def get(self, request):
        patients = Patient.objects.all()
        serializer = PatientSerializer(patients, many=True)
        return Response(serializer.data)
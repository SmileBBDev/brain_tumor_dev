from rest_framework import serializers
from .models import DoctorSchedule


class DoctorScheduleListSerializer(serializers.ModelSerializer):
    """목록 조회용 Serializer"""
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    schedule_type_display = serializers.CharField(
        source='get_schedule_type_display', read_only=True
    )
    display_color = serializers.CharField(read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_name',
            'title', 'schedule_type', 'schedule_type_display',
            'start_datetime', 'end_datetime', 'all_day',
            'color', 'display_color',
            'created_at',
        ]
        read_only_fields = fields


class DoctorScheduleDetailSerializer(serializers.ModelSerializer):
    """상세 조회용 Serializer"""
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    schedule_type_display = serializers.CharField(
        source='get_schedule_type_display', read_only=True
    )
    display_color = serializers.CharField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_name',
            'title', 'schedule_type', 'schedule_type_display',
            'description',
            'start_datetime', 'end_datetime', 'all_day',
            'color', 'display_color', 'duration_hours',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'doctor', 'doctor_name',
            'schedule_type_display', 'display_color', 'duration_hours',
            'created_at', 'updated_at',
        ]


class DoctorScheduleCreateSerializer(serializers.ModelSerializer):
    """생성용 Serializer"""

    class Meta:
        model = DoctorSchedule
        fields = [
            'title', 'schedule_type', 'description',
            'start_datetime', 'end_datetime', 'all_day',
            'color',
        ]

    def validate(self, attrs):
        """시작/종료 일시 검증"""
        start = attrs.get('start_datetime')
        end = attrs.get('end_datetime')

        if start and end and end <= start:
            raise serializers.ValidationError({
                'end_datetime': '종료 일시는 시작 일시 이후여야 합니다.'
            })

        return attrs

    def create(self, validated_data):
        """생성 시 현재 사용자를 doctor로 설정"""
        request = self.context.get('request')
        return DoctorSchedule.objects.create(
            doctor=request.user,
            **validated_data
        )


class DoctorScheduleUpdateSerializer(serializers.ModelSerializer):
    """수정용 Serializer"""

    class Meta:
        model = DoctorSchedule
        fields = [
            'title', 'schedule_type', 'description',
            'start_datetime', 'end_datetime', 'all_day',
            'color',
        ]

    def validate(self, attrs):
        """시작/종료 일시 검증"""
        start = attrs.get('start_datetime', self.instance.start_datetime)
        end = attrs.get('end_datetime', self.instance.end_datetime)

        if start and end and end <= start:
            raise serializers.ValidationError({
                'end_datetime': '종료 일시는 시작 일시 이후여야 합니다.'
            })

        return attrs


class DoctorScheduleCalendarSerializer(serializers.ModelSerializer):
    """캘린더 표시용 간소화 Serializer"""
    # 프론트엔드 CalendarScheduleItem 타입과 필드명 일치
    start = serializers.DateTimeField(source='start_datetime', read_only=True)
    end = serializers.DateTimeField(source='end_datetime', read_only=True)
    color = serializers.CharField(source='display_color', read_only=True)
    schedule_type_display = serializers.CharField(
        source='get_schedule_type_display', read_only=True
    )

    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'title', 'schedule_type', 'schedule_type_display',
            'start', 'end', 'all_day',
            'color',
        ]
        read_only_fields = fields

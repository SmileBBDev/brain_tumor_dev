"""
FHIR Admin

Django Admin 인터페이스 설정
"""
from django.contrib import admin
from .models import FHIRResourceMap, FHIRSyncQueue


@admin.register(FHIRResourceMap)
class FHIRResourceMapAdmin(admin.ModelAdmin):
    """
    FHIR Resource Map Admin

    CDSS ID ↔ FHIR ID 매핑 관리
    """
    list_display = [
        'map_id',
        'resource_type',
        'cdss_id',
        'fhir_id',
        'last_synced_at',
        'created_at'
    ]
    list_filter = ['resource_type', 'created_at', 'last_synced_at']
    search_fields = ['cdss_id', 'fhir_id', 'resource_type']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('resource_type', 'cdss_id', 'fhir_id')
        }),
        ('서버 정보', {
            'fields': ('fhir_server_url', 'last_synced_at')
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FHIRSyncQueue)
class FHIRSyncQueueAdmin(admin.ModelAdmin):
    """
    FHIR Sync Queue Admin

    FHIR 동기화 작업 큐 관리
    """
    list_display = [
        'queue_id',
        'resource_map',
        'operation',
        'status',
        'priority',
        'retry_count',
        'scheduled_at',
        'started_at',
        'completed_at'
    ]
    list_filter = [
        'status',
        'operation',
        'priority',
        'scheduled_at',
        'resource_map__resource_type'
    ]
    search_fields = [
        'queue_id',
        'resource_map__cdss_id',
        'resource_map__fhir_id',
        'error_message'
    ]
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    ordering = ['priority', 'scheduled_at']

    fieldsets = (
        ('작업 정보', {
            'fields': ('resource_map', 'operation', 'status')
        }),
        ('우선순위 및 재시도', {
            'fields': ('priority', 'retry_count', 'max_retries')
        }),
        ('실행 시간', {
            'fields': ('scheduled_at', 'started_at', 'completed_at')
        }),
        ('페이로드', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('에러 정보', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """관련 객체 prefetch"""
        qs = super().get_queryset(request)
        return qs.select_related('resource_map')

    actions = ['mark_as_pending', 'mark_as_failed']

    def mark_as_pending(self, request, queryset):
        """선택된 작업을 pending 상태로 변경"""
        updated = queryset.filter(status='failed').update(status='pending')
        self.message_user(request, f'{updated}개 작업을 pending 상태로 변경했습니다.')
    mark_as_pending.short_description = '선택된 작업을 pending 상태로 변경'

    def mark_as_failed(self, request, queryset):
        """선택된 작업을 failed 상태로 변경"""
        updated = queryset.filter(status__in=['pending', 'processing']).update(status='failed')
        self.message_user(request, f'{updated}개 작업을 failed 상태로 변경했습니다.')
    mark_as_failed.short_description = '선택된 작업을 failed 상태로 변경'

from django.contrib import admin
from .models import Claim, ValidationJob


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_id', 'service_code', 'status', 'error_type', 'paid_amount_aed', 'created_at']
    list_filter = ['status', 'error_type', 'encounter_type', 'service_code']
    search_fields = ['claim_id', 'national_id', 'member_id', 'facility_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(ValidationJob)
class ValidationJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'status', 'total_claims', 'processed_claims', 'validated_count', 'error_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job_id']
    readonly_fields = ['job_id', 'created_at', 'completed_at']
    ordering = ['-created_at']

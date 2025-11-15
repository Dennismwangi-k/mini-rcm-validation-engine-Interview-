from django.contrib import admin
from .models import RuleSet, TechnicalRule, MedicalRule


@admin.register(RuleSet)
class RuleSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'paid_amount_threshold', 'created_at']
    list_filter = ['is_active', 'created_at']


@admin.register(TechnicalRule)
class TechnicalRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_set', 'rule_type', 'service_code', 'diagnosis_code', 'requires_approval']
    list_filter = ['rule_set', 'rule_type', 'requires_approval']


@admin.register(MedicalRule)
class MedicalRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_set', 'rule_type', 'service_code', 'encounter_type', 'facility_type']
    list_filter = ['rule_set', 'rule_type', 'facility_type']

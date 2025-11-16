from rest_framework import serializers
from .models import Claim, ValidationJob, RefinedClaim, Metrics
from django.contrib.auth.models import User


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claim model"""
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    validated_by_username = serializers.CharField(source='validated_by.username', read_only=True)
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_id', 'encounter_type', 'service_date', 'national_id',
            'member_id', 'facility_id', 'unique_id', 'diagnosis_codes',
            'service_code', 'paid_amount_aed', 'approval_number',
            'status', 'error_type', 'error_explanation', 'recommended_action',
            'created_at', 'updated_at', 'uploaded_by_username', 'validated_by_username'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by_username', 'validated_by_username']


class ValidationJobSerializer(serializers.ModelSerializer):
    """Serializer for ValidationJob model"""
    
    def validate_claims_file(self, value):
        """Validate claims file"""
        if not value:
            raise serializers.ValidationError("Claims file is required")
        
        # Check file extension
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("Claims file must be an Excel file (.xlsx or .xls)")
        
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("Claims file size must be less than 50MB")
        
        return value
    
    def validate_technical_rules_file(self, value):
        """Validate technical rules file"""
        if value:
            if not value.name.endswith('.pdf'):
                raise serializers.ValidationError("Technical rules file must be a PDF file")
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Technical rules file size must be less than 10MB")
        return value
    
    def validate_medical_rules_file(self, value):
        """Validate medical rules file"""
        if value:
            if not value.name.endswith('.pdf'):
                raise serializers.ValidationError("Medical rules file must be a PDF file")
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Medical rules file size must be less than 10MB")
        return value
    
    class Meta:
        model = ValidationJob
        fields = [
            'id', 'job_id', 'status', 'claims_file', 'technical_rules_file',
            'medical_rules_file', 'total_claims', 'processed_claims',
            'validated_count', 'error_count', 'error_message',
            'data_validation_completed', 'static_rule_evaluation_completed',
            'llm_evaluation_completed', 'analytics_pipeline_completed', 'metrics_generated',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'job_id', 'status', 'total_claims', 'processed_claims',
            'validated_count', 'error_count', 'error_message',
            'data_validation_completed', 'static_rule_evaluation_completed',
            'llm_evaluation_completed', 'analytics_pipeline_completed', 'metrics_generated',
            'created_at', 'completed_at'
        ]


class RefinedClaimSerializer(serializers.ModelSerializer):
    """Serializer for RefinedClaim model"""
    claim_id = serializers.CharField(source='claim.claim_id', read_only=True)
    
    class Meta:
        model = RefinedClaim
        fields = [
            'id', 'claim', 'claim_id', 'service_code', 'paid_amount_aed',
            'status', 'error_type', 'error_explanation', 'recommended_action',
            'static_rule_validated', 'llm_validated', 'static_rule_errors', 'llm_analysis',
            'processed_at', 'updated_at', 'processed_by_job'
        ]
        read_only_fields = ['id', 'processed_at', 'updated_at']


class MetricsSerializer(serializers.ModelSerializer):
    """Serializer for Metrics model"""
    
    class Meta:
        model = Metrics
        fields = [
            'id', 'period_start', 'period_end', 'period_type', 'job',
            'total_claims', 'validated_count', 'not_validated_count',
            'no_error_count', 'medical_error_count', 'technical_error_count', 'both_error_count',
            'paid_amount_no_error', 'paid_amount_medical_error',
            'paid_amount_technical_error', 'paid_amount_both_error',
            'validation_rate', 'static_rule_processed_count', 'llm_processed_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']


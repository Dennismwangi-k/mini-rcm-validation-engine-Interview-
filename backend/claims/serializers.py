from rest_framework import serializers
from .models import Claim, ValidationJob
from django.contrib.auth.models import User


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claim model"""
    
    class Meta:
        model = Claim
        fields = [
            'id', 'claim_id', 'encounter_type', 'service_date', 'national_id',
            'member_id', 'facility_id', 'unique_id', 'diagnosis_codes',
            'service_code', 'paid_amount_aed', 'approval_number',
            'status', 'error_type', 'error_explanation', 'recommended_action',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ValidationJobSerializer(serializers.ModelSerializer):
    """Serializer for ValidationJob model"""
    
    class Meta:
        model = ValidationJob
        fields = [
            'id', 'job_id', 'status', 'claims_file', 'technical_rules_file',
            'medical_rules_file', 'total_claims', 'processed_claims',
            'validated_count', 'error_count', 'error_message',
            'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'job_id', 'status', 'total_claims', 'processed_claims',
            'validated_count', 'error_count', 'error_message', 'created_at', 'completed_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']


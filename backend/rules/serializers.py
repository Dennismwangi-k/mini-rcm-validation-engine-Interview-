from rest_framework import serializers
from .models import RuleSet, TechnicalRule, MedicalRule


class RuleSetSerializer(serializers.ModelSerializer):
    """Serializer for RuleSet model"""
    
    technical_rules_file_url = serializers.SerializerMethodField()
    medical_rules_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = RuleSet
        fields = [
            'id', 'name', 'description', 'is_active',
            'technical_rules_file', 'medical_rules_file',
            'technical_rules_file_url', 'medical_rules_file_url',
            'paid_amount_threshold', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'technical_rules_file_url', 'medical_rules_file_url']
    
    def get_technical_rules_file_url(self, obj):
        """Get URL for technical rules file"""
        if obj.technical_rules_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.technical_rules_file.url)
            return obj.technical_rules_file.url
        return None
    
    def get_medical_rules_file_url(self, obj):
        """Get URL for medical rules file"""
        if obj.medical_rules_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.medical_rules_file.url)
            return obj.medical_rules_file.url
        return None
    
    def validate_paid_amount_threshold(self, value):
        """Validate paid amount threshold"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Paid amount threshold must be non-negative.")
        return value
    
    def validate(self, attrs):
        """Validate that only one RuleSet is active"""
        is_active = attrs.get('is_active', self.instance.is_active if self.instance else False)
        if is_active:
            # If setting this RuleSet as active, deactivate all others
            existing_active = RuleSet.objects.filter(is_active=True).exclude(pk=self.instance.pk if self.instance else None)
            if existing_active.exists():
                # This will be handled in the view
                pass
        return attrs


class TechnicalRuleSerializer(serializers.ModelSerializer):
    """Serializer for TechnicalRule model"""
    
    class Meta:
        model = TechnicalRule
        fields = [
            'id', 'rule_set', 'rule_type', 'service_code', 'diagnosis_code',
            'requires_approval', 'threshold_amount', 'rule_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MedicalRuleSerializer(serializers.ModelSerializer):
    """Serializer for MedicalRule model"""
    
    class Meta:
        model = MedicalRule
        fields = [
            'id', 'rule_set', 'rule_type', 'service_code', 'encounter_type',
            'facility_id', 'facility_type', 'diagnosis_code', 'rule_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


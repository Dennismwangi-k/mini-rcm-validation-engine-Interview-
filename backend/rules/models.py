from django.db import models


class RuleSet(models.Model):
    """Multi-tenant rule set configuration"""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    technical_rules_file = models.FileField(upload_to='rules/technical/', blank=True, null=True)
    medical_rules_file = models.FileField(upload_to='rules/medical/', blank=True, null=True)
    
    # Configurable thresholds
    paid_amount_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=250.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class TechnicalRule(models.Model):
    """Parsed technical rules"""
    
    rule_set = models.ForeignKey(RuleSet, on_delete=models.CASCADE, related_name='technical_rules')
    rule_type = models.CharField(max_length=50)  # 'service_approval', 'diagnosis_approval', 'amount_threshold', 'id_format'
    service_code = models.CharField(max_length=50, blank=True, null=True)
    diagnosis_code = models.CharField(max_length=50, blank=True, null=True)
    requires_approval = models.BooleanField(default=False)
    threshold_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rule_data = models.JSONField(default=dict, help_text="Additional rule configuration")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rule_set', 'rule_type', 'service_code', 'diagnosis_code']
    
    def __str__(self):
        return f"{self.rule_type} - {self.service_code or self.diagnosis_code or 'General'}"


class MedicalRule(models.Model):
    """Parsed medical rules"""
    
    rule_set = models.ForeignKey(RuleSet, on_delete=models.CASCADE, related_name='medical_rules')
    rule_type = models.CharField(max_length=50)  # 'encounter_type', 'facility_type', 'diagnosis_requirement', 'mutually_exclusive'
    service_code = models.CharField(max_length=50, blank=True, null=True)
    encounter_type = models.CharField(max_length=50, blank=True, null=True)
    facility_id = models.CharField(max_length=50, blank=True, null=True)
    facility_type = models.CharField(max_length=100, blank=True, null=True)
    diagnosis_code = models.CharField(max_length=50, blank=True, null=True)
    rule_data = models.JSONField(default=dict, help_text="Additional rule configuration")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rule_set', 'rule_type', 'service_code', 'encounter_type', 'facility_id', 'diagnosis_code']
    
    def __str__(self):
        return f"{self.rule_type} - {self.service_code or self.encounter_type or 'General'}"

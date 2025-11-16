from django.db import models
from django.contrib.auth.models import User


class Claim(models.Model):
    """Master table storing all claims with validation results"""
    
    STATUS_CHOICES = [
        ('validated', 'Validated'),
        ('not_validated', 'Not Validated'),
    ]
    
    ERROR_TYPE_CHOICES = [
        ('no_error', 'No Error'),
        ('medical_error', 'Medical Error'),
        ('technical_error', 'Technical Error'),
        ('both', 'Both'),
    ]
    
    # Original claim data
    claim_id = models.CharField(max_length=255, unique=True, db_index=True)
    encounter_type = models.CharField(max_length=50)
    service_date = models.DateField()
    national_id = models.CharField(max_length=50)
    member_id = models.CharField(max_length=50)
    facility_id = models.CharField(max_length=50)
    unique_id = models.CharField(max_length=50)
    diagnosis_codes = models.TextField(help_text="Comma-separated diagnosis codes")
    service_code = models.CharField(max_length=50)
    paid_amount_aed = models.DecimalField(max_digits=10, decimal_places=2)
    approval_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Validation results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_validated')
    error_type = models.CharField(max_length=20, choices=ERROR_TYPE_CHOICES, default='no_error')
    error_explanation = models.TextField(blank=True, help_text="Detailed explanation of errors")
    recommended_action = models.TextField(blank=True, help_text="Actionable recommendations")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_claims')
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_claims')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['error_type']),
            models.Index(fields=['service_code']),
        ]
    
    def __str__(self):
        return f"Claim {self.claim_id} - {self.status}"


class RefinedClaim(models.Model):
    """Refined table - stores validated claims after processing through analytics pipeline"""

    # Reference to master table claim
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, related_name='refined_claim')

    # Refined/processed data (claim_id is accessible via claim.claim_id)
    service_code = models.CharField(max_length=50, db_index=True)
    paid_amount_aed = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Validation results (from analytics pipeline)
    status = models.CharField(max_length=20, choices=Claim.STATUS_CHOICES)
    error_type = models.CharField(max_length=20, choices=Claim.ERROR_TYPE_CHOICES)
    error_explanation = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    
    # Analytics pipeline flags
    static_rule_validated = models.BooleanField(default=False)
    llm_validated = models.BooleanField(default=False)
    static_rule_errors = models.TextField(blank=True, help_text="Errors from static rule evaluation")
    llm_analysis = models.TextField(blank=True, help_text="LLM-based analysis and recommendations")
    
    # Metadata
    processed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_by_job = models.ForeignKey('ValidationJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='refined_claims')
    
    class Meta:
        ordering = ['-processed_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['error_type']),
            models.Index(fields=['service_code']),
            models.Index(fields=['static_rule_validated']),
            models.Index(fields=['llm_validated']),
        ]
    
    def __str__(self):
        return f"Refined {self.claim.claim_id} - {self.status}"


class Metrics(models.Model):
    """Metrics table - stores analytics metrics from the analytics pipeline"""
    
    # Time period for metrics
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField(db_index=True)
    period_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('job', 'Per Job'),
    ], default='job')
    
    # Reference to job if applicable
    job = models.ForeignKey('ValidationJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='metrics')
    
    # Claim counts
    total_claims = models.IntegerField(default=0)
    validated_count = models.IntegerField(default=0)
    not_validated_count = models.IntegerField(default=0)
    
    # Error type counts
    no_error_count = models.IntegerField(default=0)
    medical_error_count = models.IntegerField(default=0)
    technical_error_count = models.IntegerField(default=0)
    both_error_count = models.IntegerField(default=0)
    
    # Paid amounts by error type
    paid_amount_no_error = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount_medical_error = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount_technical_error = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount_both_error = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Validation rate
    validation_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Percentage")
    
    # Analytics pipeline metrics
    static_rule_processed_count = models.IntegerField(default=0)
    llm_processed_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end']
        indexes = [
            models.Index(fields=['period_start', 'period_end']),
            models.Index(fields=['period_type']),
            models.Index(fields=['job']),
        ]
        unique_together = [['period_start', 'period_end', 'period_type', 'job']]
    
    def __str__(self):
        return f"Metrics {self.period_type} - {self.total_claims} claims"


class ValidationJob(models.Model):
    """Track validation jobs/processing runs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    job_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    claims_file = models.FileField(upload_to='uploads/claims/')
    technical_rules_file = models.FileField(upload_to='uploads/rules/', blank=True, null=True)
    medical_rules_file = models.FileField(upload_to='uploads/rules/', blank=True, null=True)
    
    total_claims = models.IntegerField(default=0)
    processed_claims = models.IntegerField(default=0)
    validated_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    # Pipeline stages
    data_validation_completed = models.BooleanField(default=False)
    static_rule_evaluation_completed = models.BooleanField(default=False)
    llm_evaluation_completed = models.BooleanField(default=False)
    analytics_pipeline_completed = models.BooleanField(default=False)
    metrics_generated = models.BooleanField(default=False)
    
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job {self.job_id} - {self.status}"

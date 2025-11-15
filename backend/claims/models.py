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
    
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job {self.job_id} - {self.status}"

from celery import shared_task
from django.core.files.storage import default_storage
import pandas as pd
from pathlib import Path
from .models import Claim, ValidationJob
from rules.rule_parser import TechnicalRuleParser, MedicalRuleParser
from rules.rule_validator import RuleValidator
from rules.llm_validator import LLMValidator
from django.conf import settings
import uuid


@shared_task(bind=True)
def process_claims_file(self, job_id: str):
    """Process claims file asynchronously"""
    try:
        job = ValidationJob.objects.get(job_id=job_id)
        job.status = 'processing'
        job.save()
        
        # Load rules
        technical_rules = {}
        medical_rules = {}
        
        # Use default rules if not provided
        if job.technical_rules_file:
            parser = TechnicalRuleParser(job.technical_rules_file.path)
            technical_rules = parser.parse()
        else:
            # Use default technical rules file
            default_tech_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Technical_Rules.pdf'
            if default_tech_rules.exists():
                parser = TechnicalRuleParser(str(default_tech_rules))
                technical_rules = parser.parse()
        
        if job.medical_rules_file:
            parser = MedicalRuleParser(job.medical_rules_file.path)
            medical_rules = parser.parse()
        else:
            # Use default medical rules file
            default_med_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Medical_Rules.pdf'
            if default_med_rules.exists():
                parser = MedicalRuleParser(str(default_med_rules))
                medical_rules = parser.parse()
        
        # Initialize validators
        rule_validator = RuleValidator(technical_rules, medical_rules)
        llm_validator = LLMValidator()
        
        # Read claims file
        df = pd.read_excel(job.claims_file.path)
        
        # Normalize column names (handle case variations)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        job.total_claims = len(df)
        job.save()
        
        validated_count = 0
        error_count = 0
        
        # Process each claim
        for idx, row in df.iterrows():
            try:
                # Map row data to claim format
                claim_data = {
                    'claim_id': str(row.get('claim_id', row.get('claim id', f'CLAIM_{idx}'))),
                    'encounter_type': str(row.get('encounter_type', row.get('encounter type', ''))).lower(),
                    'service_date': row.get('service_date', row.get('service date', '')),
                    'national_id': str(row.get('national_id', row.get('national id', ''))),
                    'member_id': str(row.get('member_id', row.get('member id', ''))),
                    'facility_id': str(row.get('facility_id', row.get('facility id', ''))),
                    'unique_id': str(row.get('unique_id', row.get('unique id', ''))),
                    'diagnosis_codes': str(row.get('diagnosis_codes', row.get('diagnosis codes', ''))),
                    'service_code': str(row.get('service_code', row.get('service code', ''))),
                    'paid_amount_aed': float(row.get('paid_amount_aed', row.get('paid amount aed', 0))),
                    'approval_number': str(row.get('approval_number', row.get('approval number', ''))).strip() or None,
                }
                
                # Validate claim
                validation_result = rule_validator.validate_claim(claim_data)
                
                # Enhance with LLM if needed
                if validation_result['error_type'] != 'no_error':
                    llm_result = llm_validator.validate_claim(claim_data, validation_result)
                    if llm_result.get('llm_enhanced'):
                        # Merge LLM insights
                        if llm_result.get('llm_explanation'):
                            validation_result['explanations'] += f"\n\nLLM Analysis:\n{llm_result['llm_explanation']}"
                        if llm_result.get('llm_recommendations'):
                            validation_result['recommended_actions'] += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                
                # Create or update claim
                claim, created = Claim.objects.update_or_create(
                    claim_id=claim_data['claim_id'],
                    defaults={
                        'encounter_type': claim_data['encounter_type'],
                        'service_date': pd.to_datetime(claim_data['service_date']).date() if pd.notna(claim_data['service_date']) else None,
                        'national_id': claim_data['national_id'],
                        'member_id': claim_data['member_id'],
                        'facility_id': claim_data['facility_id'],
                        'unique_id': claim_data['unique_id'],
                        'diagnosis_codes': claim_data['diagnosis_codes'],
                        'service_code': claim_data['service_code'],
                        'paid_amount_aed': claim_data['paid_amount_aed'],
                        'approval_number': claim_data['approval_number'],
                        'status': validation_result['status'],
                        'error_type': validation_result['error_type'],
                        'error_explanation': validation_result['explanations'],
                        'recommended_action': validation_result['recommended_actions'],
                        'uploaded_by': job.created_by,
                    }
                )
                
                if validation_result['status'] == 'validated':
                    validated_count += 1
                else:
                    error_count += 1
                
                job.processed_claims = idx + 1
                job.validated_count = validated_count
                job.error_count = error_count
                job.save()
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing claim at row {idx}: {str(e)}")
                error_count += 1
                continue
        
        # Mark job as completed
        from django.utils import timezone
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
        return {
            'status': 'completed',
            'total': job.total_claims,
            'validated': validated_count,
            'errors': error_count
        }
    
    except ValidationJob.DoesNotExist:
        return {'status': 'failed', 'error': 'Job not found'}
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        return {'status': 'failed', 'error': str(e)}


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
        
        # Load rules - always try to load default rules
        technical_rules = {}
        medical_rules = {}
        
        # Try to load technical rules
        try:
            if job.technical_rules_file:
                parser = TechnicalRuleParser(job.technical_rules_file.path)
                technical_rules = parser.parse()
            else:
                # Use default technical rules file
                default_tech_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Technical_Rules.pdf'
                if default_tech_rules.exists():
                    parser = TechnicalRuleParser(str(default_tech_rules))
                    technical_rules = parser.parse()
                    print(f"Loaded technical rules: {len(technical_rules.get('service_approvals', {}))} service approvals, {len(technical_rules.get('diagnosis_approvals', {}))} diagnosis approvals")
                else:
                    print(f"Warning: Default technical rules file not found at {default_tech_rules}")
        except Exception as e:
            print(f"Error loading technical rules: {str(e)}")
            # Use minimal default rules
            technical_rules = {
                'service_approvals': {},
                'diagnosis_approvals': {},
                'amount_threshold': 250.00,
                'id_format_rules': {}
            }
        
        # Try to load medical rules
        try:
            if job.medical_rules_file:
                parser = MedicalRuleParser(job.medical_rules_file.path)
                medical_rules = parser.parse()
            else:
                # Use default medical rules file
                default_med_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Medical_Rules.pdf'
                if default_med_rules.exists():
                    parser = MedicalRuleParser(str(default_med_rules))
                    medical_rules = parser.parse()
                    print(f"Loaded medical rules: {len(medical_rules.get('encounter_type_restrictions', {}))} encounter restrictions, {len(medical_rules.get('facility_registry', {}))} facilities")
                else:
                    print(f"Warning: Default medical rules file not found at {default_med_rules}")
        except Exception as e:
            print(f"Error loading medical rules: {str(e)}")
            # Use minimal default rules
            medical_rules = {
                'encounter_type_restrictions': {},
                'facility_type_restrictions': {},
                'diagnosis_requirements': {},
                'facility_registry': {}
            }
        
        # Ensure we have at least default threshold
        if not technical_rules.get('amount_threshold'):
            technical_rules['amount_threshold'] = 250.00
        
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
                # Generate claim_id if missing (use index + 1 for 1-based numbering)
                claim_id = row.get('claim_id') or row.get('claim id')
                if pd.isna(claim_id) or not claim_id or str(claim_id).strip() == '':
                    claim_id = f'CLAIM_{idx + 1}'
                else:
                    claim_id = str(claim_id).strip()
                
                claim_data = {
                    'claim_id': str(claim_id),
                    'encounter_type': str(row.get('encounter_type', row.get('encounter type', ''))).lower(),
                    'service_date': row.get('service_date', row.get('service date', '')),
                    'national_id': str(row.get('national_id', row.get('national id', ''))),
                    'member_id': str(row.get('member_id', row.get('member id', ''))),
                    'facility_id': str(row.get('facility_id', row.get('facility id', ''))),
                    'unique_id': str(row.get('unique_id', row.get('unique id', ''))),
                    'diagnosis_codes': str(row.get('diagnosis_codes', row.get('diagnosis codes', ''))),
                    'service_code': str(row.get('service_code', row.get('service code', ''))),
                    'paid_amount_aed': float(row.get('paid_amount_aed', row.get('paid amount aed', 0))),
                    'approval_number': str(row.get('approval_number', row.get('approval number', ''))).strip() if pd.notna(row.get('approval_number', row.get('approval number', ''))) else None,
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
                        'validated_by': job.created_by,  # Track who validated
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


@shared_task(bind=True)
def revalidate_all_claims(self=None):
    """Revalidate all claims in database with current rules"""
    try:
        # Load rules from default files
        technical_rules = {}
        medical_rules = {}
        
        # Try to load technical rules
        try:
            default_tech_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Technical_Rules.pdf'
            if default_tech_rules.exists():
                parser = TechnicalRuleParser(str(default_tech_rules))
                technical_rules = parser.parse()
                print(f"Loaded technical rules: {len(technical_rules.get('service_approvals', {}))} service approvals")
            else:
                print(f"Warning: Default technical rules file not found at {default_tech_rules}")
        except Exception as e:
            print(f"Error loading technical rules: {str(e)}")
            technical_rules = {
                'service_approvals': {},
                'diagnosis_approvals': {},
                'amount_threshold': 250.00,
                'id_format_rules': {}
            }
        
        # Try to load medical rules
        try:
            default_med_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Medical_Rules.pdf'
            if default_med_rules.exists():
                parser = MedicalRuleParser(str(default_med_rules))
                medical_rules = parser.parse()
                print(f"Loaded medical rules: {len(medical_rules.get('encounter_type_restrictions', {}))} encounter restrictions")
            else:
                print(f"Warning: Default medical rules file not found at {default_med_rules}")
        except Exception as e:
            print(f"Error loading medical rules: {str(e)}")
            medical_rules = {
                'encounter_type_restrictions': {},
                'facility_type_restrictions': {},
                'diagnosis_requirements': {},
                'facility_registry': {}
            }
        
        # Ensure we have at least default threshold
        if not technical_rules.get('amount_threshold'):
            technical_rules['amount_threshold'] = 250.00
        
        # Initialize validators
        rule_validator = RuleValidator(technical_rules, medical_rules)
        llm_validator = LLMValidator()
        
        # Get all claims
        all_claims = Claim.objects.all()
        total = all_claims.count()
        processed = 0
        validated_count = 0
        error_count = 0
        
        print(f"Revalidating {total} claims...")
        
        # Process each claim
        for claim in all_claims:
            try:
                # Convert claim to dict format
                claim_data = {
                    'claim_id': claim.claim_id,
                    'encounter_type': claim.encounter_type,
                    'service_date': claim.service_date.isoformat() if claim.service_date else '',
                    'national_id': claim.national_id,
                    'member_id': claim.member_id,
                    'facility_id': claim.facility_id,
                    'unique_id': claim.unique_id,
                    'diagnosis_codes': claim.diagnosis_codes,
                    'service_code': claim.service_code,
                    'paid_amount_aed': float(claim.paid_amount_aed),
                    'approval_number': claim.approval_number or '',
                }
                
                # Validate claim
                validation_result = rule_validator.validate_claim(claim_data)
                
                # Enhance with LLM if needed
                if validation_result['error_type'] != 'no_error':
                    try:
                        llm_result = llm_validator.validate_claim(claim_data, validation_result)
                        if llm_result.get('llm_enhanced'):
                            if llm_result.get('llm_explanation'):
                                validation_result['explanations'] += f"\n\nLLM Analysis:\n{llm_result['llm_explanation']}"
                            if llm_result.get('llm_recommendations'):
                                validation_result['recommended_actions'] += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                    except Exception as e:
                        print(f"LLM validation failed for claim {claim.claim_id}: {str(e)}")
                
                    # Update claim with new validation results
                    claim.status = validation_result['status']
                    claim.error_type = validation_result['error_type']
                    claim.error_explanation = validation_result['explanations']
                    claim.recommended_action = validation_result['recommended_actions']
                    # Get current user from request context if available, otherwise use system user
                    from django.contrib.auth.models import User
                    try:
                        system_user = User.objects.filter(is_superuser=True).first()
                        claim.validated_by = system_user
                    except:
                        pass
                    claim.save()
                
                if validation_result['status'] == 'validated':
                    validated_count += 1
                else:
                    error_count += 1
                
                processed += 1
                
                # Update progress every 10 claims (only if Celery task is available)
                if self and processed % 10 == 0:
                    try:
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'processed': processed,
                                'total': total,
                                'validated': validated_count,
                                'errors': error_count,
                                'percentage': (processed / total * 100) if total > 0 else 0
                            }
                        )
                    except:
                        pass  # Ignore if update_state fails (sync mode)
                
            except Exception as e:
                print(f"Error revalidating claim {claim.claim_id}: {str(e)}")
                error_count += 1
                processed += 1
                continue
        
        print(f"Revalidation completed: {processed}/{total} claims processed, {validated_count} validated, {error_count} errors")
        
        return {
            'status': 'completed',
            'total': total,
            'processed': processed,
            'validated': validated_count,
            'errors': error_count
        }
        
    except Exception as e:
        print(f"Error in revalidate_all_claims: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


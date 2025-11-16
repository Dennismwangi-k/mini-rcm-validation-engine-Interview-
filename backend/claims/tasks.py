from celery import shared_task
from django.core.files.storage import default_storage
import pandas as pd
from pathlib import Path
from .models import Claim, ValidationJob, RefinedClaim, Metrics
from rules.rule_parser import TechnicalRuleParser, MedicalRuleParser
from rules.rule_validator import RuleValidator
from rules.llm_validator import LLMValidator
from rules.models import RuleSet
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
import uuid


@shared_task(bind=True)
def process_claims_file(self, job_id: str):
    """Process claims file asynchronously"""
    try:
        job = ValidationJob.objects.get(job_id=job_id)
        job.status = 'processing'
        job.save()
        
        # Load rules with multi-tenant support
        # Priority: 1. Active RuleSet, 2. Job-specific files, 3. Default files
        technical_rules = {}
        medical_rules = {}
        
        # Check for active RuleSet first (multi-tenant support)
        active_ruleset = RuleSet.objects.filter(is_active=True).first()
        threshold_override = None
        if active_ruleset:
            threshold_override = float(active_ruleset.paid_amount_threshold) if active_ruleset.paid_amount_threshold else None
            print(f"Using active RuleSet: {active_ruleset.name} (threshold: {threshold_override or 'from PDF'})")
        
        # Try to load technical rules
        try:
            # Priority 1: Active RuleSet technical rules file
            if active_ruleset and active_ruleset.technical_rules_file:
                parser = TechnicalRuleParser(active_ruleset.technical_rules_file.path)
                technical_rules = parser.parse()
                print(f"Loaded technical rules from RuleSet: {active_ruleset.name}")
            # Priority 2: Job-specific technical rules file
            elif job.technical_rules_file:
                parser = TechnicalRuleParser(job.technical_rules_file.path)
                technical_rules = parser.parse()
                print("Loaded technical rules from job file")
            # Priority 3: Default technical rules file
            else:
                default_tech_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Technical_Rules.pdf'
                if default_tech_rules.exists():
                    parser = TechnicalRuleParser(str(default_tech_rules))
                    technical_rules = parser.parse()
                    print(f"Loaded technical rules from default file: {len(technical_rules.get('service_approvals', {}))} service approvals, {len(technical_rules.get('diagnosis_approvals', {}))} diagnosis approvals")
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
            # Priority 1: Active RuleSet medical rules file
            if active_ruleset and active_ruleset.medical_rules_file:
                parser = MedicalRuleParser(active_ruleset.medical_rules_file.path)
                medical_rules = parser.parse()
                print(f"Loaded medical rules from RuleSet: {active_ruleset.name}")
            # Priority 2: Job-specific medical rules file
            elif job.medical_rules_file:
                parser = MedicalRuleParser(job.medical_rules_file.path)
                medical_rules = parser.parse()
                print("Loaded medical rules from job file")
            # Priority 3: Default medical rules file
            else:
                default_med_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Medical_Rules.pdf'
                if default_med_rules.exists():
                    parser = MedicalRuleParser(str(default_med_rules))
                    medical_rules = parser.parse()
                    print(f"Loaded medical rules from default file: {len(medical_rules.get('encounter_type_restrictions', {}))} encounter restrictions, {len(medical_rules.get('facility_registry', {}))} facilities")
                else:
                    print(f"Warning: Default medical rules file not found at {default_med_rules}")
        except Exception as e:
            print(f"Error loading medical rules: {str(e)}")
            # Use minimal default rules
            medical_rules = {
                'encounter_type_restrictions': {},
                'facility_type_restrictions': {},
                'diagnosis_requirements': {},
                'facility_registry': {},
                'mutually_exclusive': []
            }
        
        # Apply threshold override from RuleSet (configurable without code changes)
        if threshold_override is not None:
            technical_rules['amount_threshold'] = threshold_override
            print(f"Threshold overridden by RuleSet: AED {threshold_override}")
        elif not technical_rules.get('amount_threshold'):
            technical_rules['amount_threshold'] = 250.00
            print(f"Using default threshold: AED 250.00")
        
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
                
                # ============================================
                # DATA PIPELINE: Stage 1 - Data Validation
                # ============================================
                # Validate claim data format and completeness
                # (Basic validation happens here - data type checks, required fields, etc.)
                
                # ============================================
                # DATA PIPELINE: Stage 2 - Master Table
                # ============================================
                # Store in master table (Claim)
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
                        'uploaded_by': job.created_by,
                    }
                )
                
                # ============================================
                # DATA PIPELINE: Stage 3 - Validation
                # ============================================
                # ANALYTICS PIPELINE Component 1: Static Rule Evaluation
                static_validation_result = rule_validator.validate_claim(claim_data)
                static_rule_validated = True
                static_rule_errors = static_validation_result.get('explanations', '')
                
                # ANALYTICS PIPELINE Component 2: LLM-based Evaluation
                llm_validated = False
                llm_analysis = ''
                final_validation_result = static_validation_result.copy()
                
                if static_validation_result['error_type'] != 'no_error':
                    try:
                        llm_result = llm_validator.validate_claim(claim_data, static_validation_result)
                        llm_validated = True
                        if llm_result.get('llm_enhanced'):
                            # Merge LLM insights
                            if llm_result.get('llm_explanation'):
                                llm_analysis = llm_result['llm_explanation']
                                final_validation_result['explanations'] += f"\n\nLLM Analysis:\n{llm_result['llm_explanation']}"
                            if llm_result.get('llm_recommendations'):
                                llm_analysis += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                                final_validation_result['recommended_actions'] += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                    except Exception as e:
                        print(f"LLM validation failed for claim {claim_data['claim_id']}: {str(e)}")
                        llm_analysis = f"LLM validation skipped: {str(e)}"
                
                # Update master table with final validation results
                claim.status = final_validation_result['status']
                claim.error_type = final_validation_result['error_type']
                claim.error_explanation = final_validation_result['explanations']
                claim.recommended_action = final_validation_result['recommended_actions']
                claim.validated_by = job.created_by
                claim.save()
                
                # ============================================
                # DATA PIPELINE: Stage 4 - Refined Table
                # ============================================
                # Store validated/refined claim in RefinedClaim table
                refined_claim, refined_created = RefinedClaim.objects.update_or_create(
                    claim=claim,
                    defaults={
                        'service_code': claim.service_code,
                        'paid_amount_aed': claim.paid_amount_aed,
                        'status': final_validation_result['status'],
                        'error_type': final_validation_result['error_type'],
                        'error_explanation': final_validation_result['explanations'],
                        'recommended_action': final_validation_result['recommended_actions'],
                        'static_rule_validated': static_rule_validated,
                        'llm_validated': llm_validated,
                        'static_rule_errors': static_rule_errors,
                        'llm_analysis': llm_analysis,
                        'processed_by_job': job,
                    }
                )
                
                if final_validation_result['status'] == 'validated':
                    validated_count += 1
                else:
                    error_count += 1
                
                job.processed_claims = idx + 1
                job.validated_count = validated_count
                job.error_count = error_count
                job.data_validation_completed = True
                job.static_rule_evaluation_completed = True
                job.llm_evaluation_completed = True
                job.analytics_pipeline_completed = True
                job.save()
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing claim at row {idx}: {str(e)}")
                error_count += 1
                continue
        
        # ============================================
        # DATA PIPELINE: Stage 5 - Analytics Pipeline → Metrics Table
        # ============================================
        # Generate metrics from refined claims
        print("Generating metrics from refined claims...")
        generate_metrics_for_job(job)
        job.metrics_generated = True
        job.save()
        
        # Mark job as completed
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


def generate_metrics_for_job(job: ValidationJob):
    """Generate metrics from refined claims for a specific job"""
    try:
        # Get all refined claims for this job
        refined_claims = RefinedClaim.objects.filter(processed_by_job=job)
        
        if not refined_claims.exists():
            print(f"No refined claims found for job {job.job_id}")
            return
        
        # Calculate metrics
        total_claims = refined_claims.count()
        validated_count = refined_claims.filter(status='validated').count()
        not_validated_count = refined_claims.filter(status='not_validated').count()
        
        # Error type counts
        no_error_count = refined_claims.filter(error_type='no_error').count()
        medical_error_count = refined_claims.filter(error_type='medical_error').count()
        technical_error_count = refined_claims.filter(error_type='technical_error').count()
        both_error_count = refined_claims.filter(error_type='both').count()
        
        # Paid amounts by error type
        paid_amount_no_error = refined_claims.filter(error_type='no_error').aggregate(
            total=Sum('paid_amount_aed')
        )['total'] or Decimal('0.00')
        
        paid_amount_medical_error = refined_claims.filter(error_type='medical_error').aggregate(
            total=Sum('paid_amount_aed')
        )['total'] or Decimal('0.00')
        
        paid_amount_technical_error = refined_claims.filter(error_type='technical_error').aggregate(
            total=Sum('paid_amount_aed')
        )['total'] or Decimal('0.00')
        
        paid_amount_both_error = refined_claims.filter(error_type='both').aggregate(
            total=Sum('paid_amount_aed')
        )['total'] or Decimal('0.00')
        
        # Validation rate
        validation_rate = (validated_count / total_claims * 100) if total_claims > 0 else Decimal('0.00')
        
        # Analytics pipeline metrics
        static_rule_processed_count = refined_claims.filter(static_rule_validated=True).count()
        llm_processed_count = refined_claims.filter(llm_validated=True).count()
        
        # Create or update metrics
        period_start = job.created_at
        period_end = job.completed_at or timezone.now()
        
        metrics, created = Metrics.objects.update_or_create(
            job=job,
            period_type='job',
            defaults={
                'period_start': period_start,
                'period_end': period_end,
                'total_claims': total_claims,
                'validated_count': validated_count,
                'not_validated_count': not_validated_count,
                'no_error_count': no_error_count,
                'medical_error_count': medical_error_count,
                'technical_error_count': technical_error_count,
                'both_error_count': both_error_count,
                'paid_amount_no_error': paid_amount_no_error,
                'paid_amount_medical_error': paid_amount_medical_error,
                'paid_amount_technical_error': paid_amount_technical_error,
                'paid_amount_both_error': paid_amount_both_error,
                'validation_rate': validation_rate,
                'static_rule_processed_count': static_rule_processed_count,
                'llm_processed_count': llm_processed_count,
            }
        )
        
        print(f"Metrics generated for job {job.job_id}: {total_claims} claims, {validated_count} validated, {validation_rate:.2f}% rate")
        
    except Exception as e:
        print(f"Error generating metrics for job {job.job_id}: {str(e)}")


@shared_task(bind=True)
def revalidate_all_claims(self=None, user_id=None):
    """Revalidate all claims in database with current rules"""
    try:
        from django.contrib.auth.models import User
        
        # Get the user who triggered the revalidation
        validated_by_user = None
        if user_id:
            try:
                validated_by_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass
        
        # Fallback to system user if no user provided
        if not validated_by_user:
            validated_by_user = User.objects.filter(is_superuser=True).first()
        
        # Load rules with multi-tenant support (same logic as process_claims_file)
        technical_rules = {}
        medical_rules = {}
        
        # Check for active RuleSet first (multi-tenant support)
        active_ruleset = RuleSet.objects.filter(is_active=True).first()
        threshold_override = None
        if active_ruleset:
            threshold_override = float(active_ruleset.paid_amount_threshold) if active_ruleset.paid_amount_threshold else None
            print(f"Using active RuleSet: {active_ruleset.name} (threshold: {threshold_override or 'from PDF'})")
        
        # Try to load technical rules
        try:
            # Priority 1: Active RuleSet technical rules file
            if active_ruleset and active_ruleset.technical_rules_file:
                parser = TechnicalRuleParser(active_ruleset.technical_rules_file.path)
                technical_rules = parser.parse()
                print(f"Loaded technical rules from RuleSet: {active_ruleset.name}")
            # Priority 2: Default technical rules file
            else:
                default_tech_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Technical_Rules.pdf'
                if default_tech_rules.exists():
                    parser = TechnicalRuleParser(str(default_tech_rules))
                    technical_rules = parser.parse()
                    print(f"Loaded technical rules from default file: {len(technical_rules.get('service_approvals', {}))} service approvals")
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
            # Priority 1: Active RuleSet medical rules file
            if active_ruleset and active_ruleset.medical_rules_file:
                parser = MedicalRuleParser(active_ruleset.medical_rules_file.path)
                medical_rules = parser.parse()
                print(f"Loaded medical rules from RuleSet: {active_ruleset.name}")
            # Priority 2: Default medical rules file
            else:
                default_med_rules = Path(settings.TENANT_CONFIG_PATH) / 'Humaein_Medical_Rules.pdf'
                if default_med_rules.exists():
                    parser = MedicalRuleParser(str(default_med_rules))
                    medical_rules = parser.parse()
                    print(f"Loaded medical rules from default file: {len(medical_rules.get('encounter_type_restrictions', {}))} encounter restrictions")
                else:
                    print(f"Warning: Default medical rules file not found at {default_med_rules}")
        except Exception as e:
            print(f"Error loading medical rules: {str(e)}")
            medical_rules = {
                'encounter_type_restrictions': {},
                'facility_type_restrictions': {},
                'diagnosis_requirements': {},
                'facility_registry': {},
                'mutually_exclusive': []
            }
        
        # Apply threshold override from RuleSet (configurable without code changes)
        if threshold_override is not None:
            technical_rules['amount_threshold'] = threshold_override
            print(f"Threshold overridden by RuleSet: AED {threshold_override}")
        elif not technical_rules.get('amount_threshold'):
            technical_rules['amount_threshold'] = 250.00
            print(f"Using default threshold: AED 250.00")
        
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
        
        # Process each claim through full data pipeline
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
                
                # ============================================
                # DATA PIPELINE: Stage 3 - Validation
                # ============================================
                # ANALYTICS PIPELINE Component 1: Static Rule Evaluation
                static_validation_result = rule_validator.validate_claim(claim_data)
                static_rule_validated = True
                static_rule_errors = static_validation_result.get('explanations', '')
                
                # ANALYTICS PIPELINE Component 2: LLM-based Evaluation
                llm_validated = False
                llm_analysis = ''
                final_validation_result = static_validation_result.copy()
                
                if static_validation_result['error_type'] != 'no_error':
                    try:
                        llm_result = llm_validator.validate_claim(claim_data, static_validation_result)
                        llm_validated = True
                        if llm_result.get('llm_enhanced'):
                            if llm_result.get('llm_explanation'):
                                llm_analysis = llm_result['llm_explanation']
                                final_validation_result['explanations'] += f"\n\nLLM Analysis:\n{llm_result['llm_explanation']}"
                            if llm_result.get('llm_recommendations'):
                                llm_analysis += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                                final_validation_result['recommended_actions'] += f"\n\nLLM Recommendations:\n{llm_result['llm_recommendations']}"
                    except Exception as e:
                        print(f"LLM validation failed for claim {claim.claim_id}: {str(e)}")
                        llm_analysis = f"LLM validation skipped: {str(e)}"
                
                # Update master table with final validation results
                claim.status = final_validation_result['status']
                claim.error_type = final_validation_result['error_type']
                claim.error_explanation = final_validation_result['explanations']
                claim.recommended_action = final_validation_result['recommended_actions']
                claim.validated_by = validated_by_user
                claim.save()
                
                # ============================================
                # DATA PIPELINE: Stage 4 - Refined Table
                # ============================================
                # Store validated/refined claim in RefinedClaim table
                refined_claim, refined_created = RefinedClaim.objects.update_or_create(
                    claim=claim,
                    defaults={
                        'service_code': claim.service_code,
                        'paid_amount_aed': claim.paid_amount_aed,
                        'status': final_validation_result['status'],
                        'error_type': final_validation_result['error_type'],
                        'error_explanation': final_validation_result['explanations'],
                        'recommended_action': final_validation_result['recommended_actions'],
                        'static_rule_validated': static_rule_validated,
                        'llm_validated': llm_validated,
                        'static_rule_errors': static_rule_errors,
                        'llm_analysis': llm_analysis,
                        'processed_by_job': None,  # Revalidation doesn't have a job
                    }
                )
                
                if final_validation_result['status'] == 'validated':
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
        
        # ============================================
        # DATA PIPELINE: Stage 5 - Analytics Pipeline → Metrics Table
        # ============================================
        # Generate overall metrics from all refined claims
        print("Generating overall metrics from refined claims...")
        try:
            from .models import RefinedClaim
            refined_claims = RefinedClaim.objects.all()
            
            if refined_claims.exists():
                # Calculate aggregate metrics
                total_refined = refined_claims.count()
                validated_refined = refined_claims.filter(status='validated').count()
                not_validated_refined = refined_claims.filter(status='not_validated').count()
                
                no_error_count = refined_claims.filter(error_type='no_error').count()
                medical_error_count = refined_claims.filter(error_type='medical_error').count()
                technical_error_count = refined_claims.filter(error_type='technical_error').count()
                both_error_count = refined_claims.filter(error_type='both').count()
                
                paid_amount_no_error = refined_claims.filter(error_type='no_error').aggregate(total=Sum('paid_amount_aed'))['total'] or Decimal('0.00')
                paid_amount_medical_error = refined_claims.filter(error_type='medical_error').aggregate(total=Sum('paid_amount_aed'))['total'] or Decimal('0.00')
                paid_amount_technical_error = refined_claims.filter(error_type='technical_error').aggregate(total=Sum('paid_amount_aed'))['total'] or Decimal('0.00')
                paid_amount_both_error = refined_claims.filter(error_type='both').aggregate(total=Sum('paid_amount_aed'))['total'] or Decimal('0.00')
                
                validation_rate = (validated_refined / total_refined * 100) if total_refined > 0 else Decimal('0.00')
                static_rule_processed_count = refined_claims.filter(static_rule_validated=True).count()
                llm_processed_count = refined_claims.filter(llm_validated=True).count()
                
                # Create overall metrics (no job association for revalidation)
                period_start = timezone.now() - timezone.timedelta(days=1)
                period_end = timezone.now()
                
                Metrics.objects.update_or_create(
                    job=None,
                    period_type='job',
                    period_start=period_start,
                    period_end=period_end,
                    defaults={
                        'total_claims': total_refined,
                        'validated_count': validated_refined,
                        'not_validated_count': not_validated_refined,
                        'no_error_count': no_error_count,
                        'medical_error_count': medical_error_count,
                        'technical_error_count': technical_error_count,
                        'both_error_count': both_error_count,
                        'paid_amount_no_error': paid_amount_no_error,
                        'paid_amount_medical_error': paid_amount_medical_error,
                        'paid_amount_technical_error': paid_amount_technical_error,
                        'paid_amount_both_error': paid_amount_both_error,
                        'validation_rate': validation_rate,
                        'static_rule_processed_count': static_rule_processed_count,
                        'llm_processed_count': llm_processed_count,
                    }
                )
                print(f"Overall metrics generated: {total_refined} claims, {validated_refined} validated, {validation_rate:.2f}% rate")
        except Exception as e:
            print(f"Error generating overall metrics: {str(e)}")
        
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


import re
from typing import Dict, List, Tuple, Any
from decimal import Decimal


class RuleValidator:
    """Validate claims against technical and medical rules"""
    
    def __init__(self, technical_rules: Dict, medical_rules: Dict):
        self.technical_rules = technical_rules
        self.medical_rules = medical_rules
    
    def validate_claim(self, claim_data: Dict) -> Dict[str, Any]:
        """
        Validate a single claim and return results
        
        Returns:
            {
                'status': 'validated' or 'not_validated',
                'error_type': 'no_error', 'medical_error', 'technical_error', 'both',
                'errors': List of error messages,
                'explanations': List of detailed explanations,
                'recommended_actions': List of recommended actions
            }
        """
        errors = []
        explanations = []
        recommended_actions = []
        
        # Technical validation
        technical_errors = self._validate_technical(claim_data)
        errors.extend(technical_errors['errors'])
        explanations.extend(technical_errors['explanations'])
        recommended_actions.extend(technical_errors['recommended_actions'])
        
        # Medical validation
        medical_errors = self._validate_medical(claim_data)
        errors.extend(medical_errors['errors'])
        explanations.extend(medical_errors['explanations'])
        recommended_actions.extend(medical_errors['recommended_actions'])
        
        # Determine status and error type
        has_technical_error = len(technical_errors['errors']) > 0
        has_medical_error = len(medical_errors['errors']) > 0
        
        if has_technical_error and has_medical_error:
            error_type = 'both'
        elif has_technical_error:
            error_type = 'technical_error'
        elif has_medical_error:
            error_type = 'medical_error'
        else:
            error_type = 'no_error'
        
        status = 'validated' if error_type == 'no_error' else 'not_validated'
        
        return {
            'status': status,
            'error_type': error_type,
            'errors': errors,
            'explanations': '\n'.join([f"• {exp}" for exp in explanations]),
            'recommended_actions': '\n'.join([f"• {action}" for action in recommended_actions])
        }
    
    def _validate_technical(self, claim: Dict) -> Dict[str, List[str]]:
        """Validate against technical rules"""
        errors = []
        explanations = []
        recommended_actions = []
        
        # Helper function to check if approval is valid
        def has_valid_approval(approval_value):
            """Check if approval number is valid (not None, empty, NaN, or placeholder text)"""
            if not approval_value:
                return False
            approval_str = str(approval_value).strip().upper()
            # Treat placeholder text as invalid
            invalid_placeholders = ['OBTAIN APPROVAL', 'NAN', 'NONE', '']
            return approval_str not in invalid_placeholders
        
        # 1. Check service code approval requirement
        service_code = claim.get('service_code', '')
        service_rules = self.technical_rules.get('service_approvals', {})
        
        if service_code in service_rules:
            requires_approval = service_rules[service_code].get('requires_approval', False)
            if requires_approval and not has_valid_approval(claim.get('approval_number')):
                errors.append('Missing approval for service requiring prior approval')
                explanations.append(
                    f"Service code {service_code} ({service_rules[service_code].get('description', '')}) "
                    f"requires prior approval, but no valid approval number was provided."
                )
                recommended_actions.append(
                    f"Obtain prior approval for service {service_code} before submitting the claim."
                )
        
        # 2. Check diagnosis code approval requirement
        diagnosis_codes = [d.strip() for d in claim.get('diagnosis_codes', '').split(',') if d.strip()]
        diagnosis_rules = self.technical_rules.get('diagnosis_approvals', {})
        
        for diag_code in diagnosis_codes:
            if diag_code in diagnosis_rules:
                requires_approval = diagnosis_rules[diag_code].get('requires_approval', False)
                if requires_approval and not has_valid_approval(claim.get('approval_number')):
                    errors.append('Missing approval for diagnosis requiring prior approval')
                    explanations.append(
                        f"Diagnosis code {diag_code} ({diagnosis_rules[diag_code].get('description', '')}) "
                        f"requires prior approval, but no valid approval number was provided."
                    )
                    recommended_actions.append(
                        f"Obtain prior approval for diagnosis {diag_code} before submitting the claim."
                    )
        
        # 3. Check paid amount threshold
        paid_amount = Decimal(str(claim.get('paid_amount_aed', 0)))
        threshold = Decimal(str(self.technical_rules.get('amount_threshold', 250)))
        
        if paid_amount > threshold and not has_valid_approval(claim.get('approval_number')):
            errors.append('Missing approval for claim exceeding amount threshold')
            explanations.append(
                f"Paid amount AED {paid_amount} exceeds the threshold of AED {threshold}, "
                f"requiring prior approval, but no valid approval number was provided."
            )
            recommended_actions.append(
                f"Obtain prior approval for claims exceeding AED {threshold}."
            )
        
        # 4. Validate ID formatting
        id_errors = self._validate_id_format(claim)
        errors.extend(id_errors['errors'])
        explanations.extend(id_errors['explanations'])
        recommended_actions.extend(id_errors['recommended_actions'])
        
        return {
            'errors': errors,
            'explanations': explanations,
            'recommended_actions': recommended_actions
        }
    
    def _validate_id_format(self, claim: Dict) -> Dict[str, List[str]]:
        """Validate ID formatting rules"""
        errors = []
        explanations = []
        recommended_actions = []
        
        # Check uppercase alphanumeric
        id_fields = {
            'national_id': claim.get('national_id', ''),
            'member_id': claim.get('member_id', ''),
            'facility_id': claim.get('facility_id', ''),
            'unique_id': claim.get('unique_id', '')
        }
        
        for field_name, field_value in id_fields.items():
            if not field_value:
                continue
            
            # Check uppercase
            if field_value != field_value.upper():
                errors.append(f'{field_name} must be uppercase')
                explanations.append(
                    f"{field_name.replace('_', ' ').title()} '{field_value}' must be in uppercase format."
                )
                recommended_actions.append(
                    f"Convert {field_name.replace('_', ' ')} to uppercase: {field_value.upper()}"
                )
            
            # Check alphanumeric
            if not re.match(r'^[A-Z0-9]+$', field_value.upper()):
                errors.append(f'{field_name} contains invalid characters')
                explanations.append(
                    f"{field_name.replace('_', ' ').title()} '{field_value}' must contain only alphanumeric characters (A-Z, 0-9)."
                )
                recommended_actions.append(
                    f"Remove special characters from {field_name.replace('_', ' ')}."
                )
        
        # Validate unique_id format: first4(National ID) – middle4(Member ID) – last4(Facility ID)
        unique_id = claim.get('unique_id', '')
        national_id = claim.get('national_id', '')
        member_id = claim.get('member_id', '')
        facility_id = claim.get('facility_id', '')
        
        if unique_id and national_id and member_id and facility_id:
            expected_format = f"{national_id[:4]}-{member_id[:4]}-{facility_id[:4]}"
            if unique_id.upper() != expected_format.upper():
                errors.append('unique_id format is incorrect')
                explanations.append(
                    f"Unique ID '{unique_id}' does not match the required format. "
                    f"Expected format: first 4 characters of National ID, middle 4 of Member ID, "
                    f"last 4 of Facility ID, hyphen-separated. Expected: {expected_format}"
                )
                recommended_actions.append(
                    f"Correct unique_id format to: {expected_format}"
                )
        
        return {
            'errors': errors,
            'explanations': explanations,
            'recommended_actions': recommended_actions
        }
    
    def _validate_medical(self, claim: Dict) -> Dict[str, List[str]]:
        """Validate against medical rules"""
        errors = []
        explanations = []
        recommended_actions = []
        
        service_code = claim.get('service_code', '')
        encounter_type = claim.get('encounter_type', '').lower()
        facility_id = claim.get('facility_id', '')
        diagnosis_codes = [d.strip() for d in claim.get('diagnosis_codes', '').split(',') if d.strip()]
        
        # 1. Check encounter type restrictions
        encounter_restrictions = self.medical_rules.get('encounter_type_restrictions', {})
        if service_code in encounter_restrictions:
            required_encounter = encounter_restrictions[service_code]
            if encounter_type != required_encounter:
                errors.append('Service not allowed for this encounter type')
                explanations.append(
                    f"Service code {service_code} is restricted to {required_encounter} encounters only, "
                    f"but the claim has encounter type '{encounter_type}'."
                )
                recommended_actions.append(
                    f"Ensure service {service_code} is only used for {required_encounter} encounters."
                )
        
        # 2. Check facility type restrictions
        facility_registry = self.medical_rules.get('facility_registry', {})
        facility_type_restrictions = self.medical_rules.get('facility_type_restrictions', {})
        
        if facility_id in facility_registry:
            facility_type = facility_registry[facility_id]
            
            if service_code in facility_type_restrictions:
                allowed_facility_types = facility_type_restrictions[service_code]
                if facility_type not in allowed_facility_types:
                    errors.append('Service not allowed at this facility type')
                    explanations.append(
                        f"Service code {service_code} is not allowed at {facility_type} facilities. "
                        f"Allowed facility types: {', '.join(allowed_facility_types)}"
                    )
                    recommended_actions.append(
                        f"Use service {service_code} only at allowed facility types: {', '.join(allowed_facility_types)}"
                    )
        
        # 3. Check diagnosis requirements
        diagnosis_requirements = self.medical_rules.get('diagnosis_requirements', {})
        if service_code in diagnosis_requirements:
            required_diagnoses = diagnosis_requirements[service_code]
            has_required_diagnosis = any(diag in required_diagnoses for diag in diagnosis_codes)
            
            if not has_required_diagnosis:
                errors.append('Missing required diagnosis for service')
                explanations.append(
                    f"Service code {service_code} requires one of the following diagnosis codes: "
                    f"{', '.join(required_diagnoses)}, but none were found in the claim."
                )
                recommended_actions.append(
                    f"Ensure service {service_code} is only used with appropriate diagnosis codes: "
                    f"{', '.join(required_diagnoses)}"
                )
        
        return {
            'errors': errors,
            'explanations': explanations,
            'recommended_actions': recommended_actions
        }


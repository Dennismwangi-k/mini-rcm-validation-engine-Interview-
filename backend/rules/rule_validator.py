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
        
        # Check uppercase alphanumeric - only for non-empty values
        id_fields = {
            'national_id': claim.get('national_id', ''),
            'member_id': claim.get('member_id', ''),
            'facility_id': claim.get('facility_id', ''),
            'unique_id': claim.get('unique_id', '')
        }
        
        for field_name, field_value in id_fields.items():
            if not field_value or str(field_value).strip() == '':
                continue
            
            field_value = str(field_value).strip()
            original_value = field_value
            
            # Check uppercase (only warn, don't fail validation for case)
            if field_value != field_value.upper():
                # Convert to uppercase for validation but don't fail
                field_value = field_value.upper()
            
            # Check alphanumeric (excluding unique_id which can have hyphens)
            if field_name != 'unique_id':
                # For non-unique_id fields, check if they contain only alphanumeric after removing hyphens
                # (in case they have hyphens that shouldn't be there)
                cleaned_value = field_value.replace('-', '').replace('_', '')
                if not re.match(r'^[A-Z0-9]+$', cleaned_value):
                    errors.append(f'{field_name} contains invalid characters')
                    explanations.append(
                        f"{field_name.replace('_', ' ').title()} '{original_value}' must contain only alphanumeric characters (A-Z, 0-9)."
                    )
                    recommended_actions.append(
                        f"Remove special characters from {field_name.replace('_', ' ')}."
                    )
        
        # Validate unique_id format: first4(National ID) – middle4(Member ID) – last4(Facility ID)
        unique_id = str(claim.get('unique_id', '')).strip().upper()
        national_id = str(claim.get('national_id', '')).strip().upper()
        member_id = str(claim.get('member_id', '')).strip().upper()
        facility_id = str(claim.get('facility_id', '')).strip().upper()
        
        if unique_id and national_id and member_id and facility_id:
            # Only validate if all IDs have at least 4 characters
            if len(national_id) >= 4 and len(member_id) >= 4 and len(facility_id) >= 4:
                expected_format = f"{national_id[:4]}-{member_id[:4]}-{facility_id[:4]}"
                # Normalize unique_id by removing hyphens for comparison
                unique_id_normalized = unique_id.replace('-', '').replace('_', '')
                expected_normalized = expected_format.replace('-', '').replace('_', '')
                
                if unique_id_normalized != expected_normalized:
                    errors.append('unique_id format is incorrect')
                    explanations.append(
                        f"Unique ID '{unique_id}' does not match the required format. "
                        f"Expected format: first 4 characters of National ID, middle 4 of Member ID, "
                        f"last 4 of Facility ID, hyphen-separated. Expected: {expected_format}"
                    )
                    recommended_actions.append(
                        f"Correct unique_id format to: {expected_format}"
                    )
        
        # Check if unique_id contains only alphanumeric and hyphens
        if unique_id and not re.match(r'^[A-Z0-9\-]+$', unique_id):
                errors.append('unique_id contains invalid characters')
                explanations.append(
                    f"Unique ID '{unique_id}' must contain only alphanumeric characters (A-Z, 0-9) and hyphens."
                )
                recommended_actions.append(
                    f"Remove invalid characters from unique_id."
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
        
        # 4. Check mutually exclusive diagnoses
        mutually_exclusive = self.medical_rules.get('mutually_exclusive', [])
        for diag_pair in mutually_exclusive:
            if len(diag_pair) == 2:
                diag1, diag2 = diag_pair
                # Normalize diagnosis codes (handle both with and without decimal points)
                diag1_normalized = diag1.replace('.', '').upper()
                diag2_normalized = diag2.replace('.', '').upper()
                
                # Check if both diagnoses are present
                has_diag1 = any(
                    d.strip().replace('.', '').upper() == diag1_normalized 
                    for d in diagnosis_codes
                )
                has_diag2 = any(
                    d.strip().replace('.', '').upper() == diag2_normalized 
                    for d in diagnosis_codes
                )
                
                if has_diag1 and has_diag2:
                    errors.append('Mutually exclusive diagnoses found on same claim')
                    explanations.append(
                        f"Diagnosis codes {diag1} and {diag2} cannot coexist on the same claim. "
                        f"Both were found in the diagnosis codes for this claim."
                    )
                    recommended_actions.append(
                        f"Remove one of the mutually exclusive diagnosis codes ({diag1} or {diag2}) from the claim."
                )
        
        return {
            'errors': errors,
            'explanations': explanations,
            'recommended_actions': recommended_actions
        }


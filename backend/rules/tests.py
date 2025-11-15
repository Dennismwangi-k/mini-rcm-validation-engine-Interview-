from django.test import TestCase
from .rule_validator import RuleValidator


class RuleValidatorTest(TestCase):
    def setUp(self):
        self.technical_rules = {
            'service_approvals': {
                'SRV1001': {'requires_approval': True, 'description': 'Major Surgery'}
            },
            'diagnosis_approvals': {
                'E11.9': {'requires_approval': True, 'description': 'Diabetes Mellitus'}
            },
            'amount_threshold': 250.00,
            'id_format_rules': {}
        }
        
        self.medical_rules = {
            'encounter_type_restrictions': {
                'SRV1001': 'inpatient'
            },
            'facility_type_restrictions': {},
            'diagnosis_requirements': {},
            'facility_registry': {}
        }
        
        self.validator = RuleValidator(self.technical_rules, self.medical_rules)
    
    def test_validate_claim_missing_approval(self):
        claim = {
            'service_code': 'SRV1001',
            'encounter_type': 'inpatient',
            'paid_amount_aed': 100.00,
            'approval_number': None,
            'diagnosis_codes': '',
            'national_id': 'ABC123',
            'member_id': 'DEF456',
            'facility_id': 'GHI789',
            'unique_id': 'ABCD-EFGH-IJKL'
        }
        
        result = self.validator.validate_claim(claim)
        self.assertEqual(result['status'], 'not_validated')
        self.assertEqual(result['error_type'], 'technical_error')
        self.assertGreater(len(result['errors']), 0)

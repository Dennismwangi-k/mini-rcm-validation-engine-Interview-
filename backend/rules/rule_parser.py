import pdfplumber
import re
from typing import Dict, List, Any
from pathlib import Path


class TechnicalRuleParser:
    """Parse technical adjudication rules from PDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.rules = {
            'service_approvals': {},
            'diagnosis_approvals': {},
            'amount_threshold': 250.00,
            'id_format_rules': {}
        }
    
    def parse(self) -> Dict[str, Any]:
        """Extract rules from PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        self._parse_service_approvals(text)
        self._parse_diagnosis_approvals(text)
        self._parse_amount_threshold(text)
        self._parse_id_format_rules(text)
        
        return self.rules
    
    def _parse_service_approvals(self, text: str):
        """Parse service codes requiring approval"""
        # Look for service code table
        lines = text.split('\n')
        in_service_table = False
        
        for i, line in enumerate(lines):
            if 'Services Requiring Prior Approval' in line or 'Service Code' in line:
                in_service_table = True
                continue
            
            if in_service_table:
                # Match service codes like SRV1001, SRV2001, etc.
                match = re.search(r'(SRV\d+)\s+([A-Za-z\s]+?)\s+(YES|NO)', line)
                if match:
                    service_code = match.group(1).strip()
                    description = match.group(2).strip()
                    requires_approval = match.group(3).strip() == 'YES'
                    self.rules['service_approvals'][service_code] = {
                        'description': description,
                        'requires_approval': requires_approval
                    }
                elif 'Diagnosis Codes' in line or 'Paid Amount' in line:
                    break
    
    def _parse_diagnosis_approvals(self, text: str):
        """Parse diagnosis codes requiring approval"""
        lines = text.split('\n')
        in_diagnosis_table = False
        
        for i, line in enumerate(lines):
            if 'Diagnosis Codes Requiring Approval' in line or 'Diagnosis Code' in line:
                in_diagnosis_table = True
                continue
            
            if in_diagnosis_table:
                # Match diagnosis codes like E11.9, R07.9, etc.
                match = re.search(r'([A-Z]\d+\.\d+)\s+([A-Za-z\s]+?)\s+(YES|NO)', line)
                if match:
                    diagnosis_code = match.group(1).strip()
                    description = match.group(2).strip()
                    requires_approval = match.group(3).strip() == 'YES'
                    self.rules['diagnosis_approvals'][diagnosis_code] = {
                        'description': description,
                        'requires_approval': requires_approval
                    }
                elif 'Paid Amount' in line or 'ID & Unique ID' in line:
                    break
    
    def _parse_amount_threshold(self, text: str):
        """Parse paid amount threshold"""
        # Look for threshold amount
        match = re.search(r'paid_amount_aed\s*>\s*AED\s*(\d+)', text, re.IGNORECASE)
        if match:
            self.rules['amount_threshold'] = float(match.group(1))
    
    def _parse_id_format_rules(self, text: str):
        """Parse ID formatting rules"""
        self.rules['id_format_rules'] = {
            'must_be_uppercase': True,
            'alphanumeric_only': True,
            'unique_id_format': 'first4(National ID) – middle4(Member ID) – last4(Facility ID)',
            'hyphen_separated': True
        }


class MedicalRuleParser:
    """Parse medical adjudication rules from PDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.rules = {
            'encounter_type_restrictions': {},
            'facility_type_restrictions': {},
            'diagnosis_requirements': {},
            'mutually_exclusive': []
        }
    
    def parse(self) -> Dict[str, Any]:
        """Extract rules from PDF"""
        with pdfplumber.open(self.pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        self._parse_encounter_type_restrictions(text)
        self._parse_facility_type_restrictions(text)
        self._parse_diagnosis_requirements(text)
        self._parse_facility_registry(text)
        
        return self.rules
    
    def _parse_encounter_type_restrictions(self, text: str):
        """Parse encounter type restrictions"""
        # Inpatient-only services
        inpatient_match = re.search(r'Inpatient-only services:([\s\S]*?)Outpatient-only services:', text)
        if inpatient_match:
            services = re.findall(r'(SRV\d+)', inpatient_match.group(1))
            for service in services:
                self.rules['encounter_type_restrictions'][service] = 'inpatient'
        
        # Outpatient-only services
        outpatient_match = re.search(r'Outpatient-only services:([\s\S]*?)(?:B\.|Services limited by Facility)', text)
        if outpatient_match:
            services = re.findall(r'(SRV\d+)', outpatient_match.group(1))
            for service in services:
                self.rules['encounter_type_restrictions'][service] = 'outpatient'
    
    def _parse_facility_type_restrictions(self, text: str):
        """Parse facility type restrictions"""
        # Parse facility type mappings
        facility_patterns = [
            (r'MATERNITY_HOSPITAL:\s*([SRV\d,\s]+)', 'MATERNITY_HOSPITAL'),
            (r'DIALYSIS_CENTER:\s*([SRV\d,\s]+)', 'DIALYSIS_CENTER'),
            (r'CARDIOLOGY_CENTER:\s*([SRV\d,\s]+)', 'CARDIOLOGY_CENTER'),
            (r'GENERAL_HOSPITAL:\s*([SRV\d,\s]+)', 'GENERAL_HOSPITAL'),
        ]
        
        for pattern, facility_type in facility_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                services = re.findall(r'(SRV\d+)', match)
                for service in services:
                    if service not in self.rules['facility_type_restrictions']:
                        self.rules['facility_type_restrictions'][service] = []
                    self.rules['facility_type_restrictions'][service].append(facility_type)
    
    def _parse_facility_registry(self, text: str):
        """Parse facility ID to facility type mapping"""
        # Extract facility registry table
        facility_registry = {}
        lines = text.split('\n')
        in_registry = False
        
        for line in lines:
            if 'Facility Registry' in line or 'IDs present in claims' in line:
                in_registry = True
                continue
            
            if in_registry:
                # Match facility ID and type: "0DBYE6KP DIALYSIS_CENTER"
                match = re.search(r'([A-Z0-9]{8,})\s+([A-Z_]+)', line)
                if match:
                    facility_id = match.group(1).strip()
                    facility_type = match.group(2).strip()
                    facility_registry[facility_id] = facility_type
                elif line.strip() and not match:
                    # End of registry
                    break
        
        self.rules['facility_registry'] = facility_registry
    
    def _parse_diagnosis_requirements(self, text: str):
        """Parse services requiring specific diagnoses"""
        # Pattern: "E11.9 Diabetes Mellitus: SRV2007 HbA1c Test"
        pattern = r'([A-Z]\d+\.\d+)\s+[^:]+:\s*(SRV\d+)'
        matches = re.findall(pattern, text)
        
        for diagnosis_code, service_code in matches:
            if service_code not in self.rules['diagnosis_requirements']:
                self.rules['diagnosis_requirements'][service_code] = []
            self.rules['diagnosis_requirements'][service_code].append(diagnosis_code)


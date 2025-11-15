import os
from typing import Dict, Any
from openai import OpenAI
from django.conf import settings


class LLMValidator:
    """Use LLM to validate claims and provide additional insights"""
    
    def __init__(self):
        api_key = settings.OPENAI_API_KEY or os.getenv('OPENAI_API_KEY', '')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def validate_claim(self, claim_data: Dict, static_validation_result: Dict) -> Dict[str, Any]:
        """
        Use LLM to provide additional validation and explanations
        
        Args:
            claim_data: The claim data
            static_validation_result: Results from static rule validation
        
        Returns:
            Enhanced validation results with LLM insights
        """
        if not self.client:
            # If no API key, return static results only
            return {
                'llm_enhanced': False,
                'llm_explanation': '',
                'llm_recommendations': ''
            }
        
        try:
            # Build prompt for LLM
            prompt = self._build_prompt(claim_data, static_validation_result)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical claims validation expert. Analyze claims and provide clear, actionable feedback."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            llm_response = response.choices[0].message.content
            
            # Parse LLM response
            return {
                'llm_enhanced': True,
                'llm_explanation': llm_response,
                'llm_recommendations': self._extract_recommendations(llm_response)
            }
        
        except Exception as e:
            # If LLM fails, fall back to static validation
            return {
                'llm_enhanced': False,
                'llm_explanation': f'LLM validation unavailable: {str(e)}',
                'llm_recommendations': ''
            }
    
    def _build_prompt(self, claim_data: Dict, static_result: Dict) -> str:
        """Build prompt for LLM"""
        prompt = f"""
Analyze this medical claim and provide validation insights:

Claim Details:
- Service Code: {claim_data.get('service_code', 'N/A')}
- Encounter Type: {claim_data.get('encounter_type', 'N/A')}
- Diagnosis Codes: {claim_data.get('diagnosis_codes', 'N/A')}
- Paid Amount: AED {claim_data.get('paid_amount_aed', 0)}
- Approval Number: {claim_data.get('approval_number', 'None')}
- Facility ID: {claim_data.get('facility_id', 'N/A')}

Static Validation Results:
- Status: {static_result.get('status', 'N/A')}
- Error Type: {static_result.get('error_type', 'N/A')}
- Errors Found: {len(static_result.get('errors', []))}

Please provide:
1. A brief explanation of any potential issues or confirmations
2. Actionable recommendations if errors exist
3. Any additional medical coding or billing insights

Keep the response concise and focused on actionable items.
"""
        return prompt
    
    def _extract_recommendations(self, llm_response: str) -> str:
        """Extract recommendations from LLM response"""
        # Simple extraction - look for recommendation sections
        lines = llm_response.split('\n')
        recommendations = []
        in_recommendations = False
        
        for line in lines:
            if 'recommend' in line.lower() or 'action' in line.lower():
                in_recommendations = True
            if in_recommendations and line.strip():
                recommendations.append(line.strip())
        
        return '\n'.join(recommendations) if recommendations else llm_response


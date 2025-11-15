from django.test import TestCase
from django.contrib.auth.models import User
from .models import Claim, ValidationJob


class ClaimModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_claim_creation(self):
        claim = Claim.objects.create(
            claim_id='TEST001',
            encounter_type='inpatient',
            service_code='SRV1001',
            paid_amount_aed=100.00,
            status='validated',
            error_type='no_error',
            uploaded_by=self.user
        )
        self.assertEqual(str(claim), 'Claim TEST001 - validated')
        self.assertEqual(claim.status, 'validated')


class ValidationJobModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_job_creation(self):
        job = ValidationJob.objects.create(
            job_id='test-job-001',
            status='pending',
            created_by=self.user
        )
        self.assertEqual(str(job), 'Job test-job-001 - pending')

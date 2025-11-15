from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Claim, ValidationJob
from .serializers import ClaimSerializer, ValidationJobSerializer
from .tasks import process_claims_file
import uuid
from django.utils import timezone


class ClaimViewSet(viewsets.ModelViewSet):
    """ViewSet for Claim model"""
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'error_type', 'service_code', 'encounter_type']
    search_fields = ['claim_id', 'national_id', 'member_id', 'facility_id']
    ordering_fields = ['created_at', 'paid_amount_aed', 'service_date']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for claims"""
        queryset = self.filter_queryset(self.get_queryset())
        
        total = queryset.count()
        validated = queryset.filter(status='validated').count()
        not_validated = queryset.filter(status='not_validated').count()
        
        error_types = {
            'no_error': queryset.filter(error_type='no_error').count(),
            'medical_error': queryset.filter(error_type='medical_error').count(),
            'technical_error': queryset.filter(error_type='technical_error').count(),
            'both': queryset.filter(error_type='both').count(),
        }
        
        # Calculate paid amounts by error category
        from django.db.models import Sum
        paid_by_error = {
            'no_error': float(queryset.filter(error_type='no_error').aggregate(total=Sum('paid_amount_aed'))['total'] or 0),
            'medical_error': float(queryset.filter(error_type='medical_error').aggregate(total=Sum('paid_amount_aed'))['total'] or 0),
            'technical_error': float(queryset.filter(error_type='technical_error').aggregate(total=Sum('paid_amount_aed'))['total'] or 0),
            'both': float(queryset.filter(error_type='both').aggregate(total=Sum('paid_amount_aed'))['total'] or 0),
        }
        
        return Response({
            'total_claims': total,
            'validated': validated,
            'not_validated': not_validated,
            'error_type_counts': error_types,
            'paid_amount_by_error': paid_by_error
        })


class ValidationJobViewSet(viewsets.ModelViewSet):
    """ViewSet for ValidationJob model"""
    queryset = ValidationJob.objects.all()
    serializer_class = ValidationJobSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def create(self, request, *args, **kwargs):
        """Create validation job and start processing"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(
            job_id=str(uuid.uuid4()),
            created_by=request.user
        )
        
        # Start async processing
        process_claims_file.delay(job.job_id)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get job status"""
        job = self.get_object()
        return Response({
            'job_id': job.job_id,
            'status': job.status,
            'progress': {
                'total': job.total_claims,
                'processed': job.processed_claims,
                'validated': job.validated_count,
                'errors': job.error_count,
                'percentage': (job.processed_claims / job.total_claims * 100) if job.total_claims > 0 else 0
            }
        })

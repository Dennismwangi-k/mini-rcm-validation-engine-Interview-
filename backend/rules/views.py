from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import RuleSet, TechnicalRule, MedicalRule
from .serializers import RuleSetSerializer, TechnicalRuleSerializer, MedicalRuleSerializer


class RuleSetViewSet(viewsets.ModelViewSet):
    """ViewSet for RuleSet model - Multi-tenant configuration"""
    
    queryset = RuleSet.objects.all()
    serializer_class = RuleSetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_context(self):
        """Add request to serializer context for file URLs"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Create rule set and handle active status"""
        is_active = serializer.validated_data.get('is_active', False)
        
        # If setting as active, deactivate all others
        if is_active:
            RuleSet.objects.filter(is_active=True).update(is_active=False)
        
        serializer.save()
    
    def perform_update(self, serializer):
        """Update rule set and handle active status"""
        is_active = serializer.validated_data.get('is_active', self.instance.is_active)
        
        # If setting as active, deactivate all others (except this one)
        if is_active and not self.instance.is_active:
            RuleSet.objects.filter(is_active=True).exclude(pk=self.instance.pk).update(is_active=False)
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set a specific rule set as active (deactivates others)"""
        ruleset = self.get_object()
        
        # Deactivate all other rule sets
        RuleSet.objects.filter(is_active=True).exclude(pk=ruleset.pk).update(is_active=False)
        
        # Activate this rule set
        ruleset.is_active = True
        ruleset.save()
        
        serializer = self.get_serializer(ruleset)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='active', url_name='active')
    def active(self, request):
        """Get the currently active rule set"""
        active_ruleset = RuleSet.objects.filter(is_active=True).first()
        
        if active_ruleset:
            serializer = self.get_serializer(active_ruleset)
            return Response(serializer.data)
        else:
            return Response({'message': 'No active rule set found'}, status=status.HTTP_404_NOT_FOUND)


class TechnicalRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for TechnicalRule model"""
    
    queryset = TechnicalRule.objects.all()
    serializer_class = TechnicalRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rule_set', 'rule_type', 'requires_approval']
    search_fields = ['service_code', 'diagnosis_code']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class MedicalRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for MedicalRule model"""
    
    queryset = MedicalRule.objects.all()
    serializer_class = MedicalRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rule_set', 'rule_type', 'facility_type']
    search_fields = ['service_code', 'diagnosis_code', 'facility_id']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

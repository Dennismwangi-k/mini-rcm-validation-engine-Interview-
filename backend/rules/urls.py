from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RuleSetViewSet, TechnicalRuleViewSet, MedicalRuleViewSet

router = DefaultRouter()
router.register(r'rulesets', RuleSetViewSet, basename='ruleset')
router.register(r'technical-rules', TechnicalRuleViewSet, basename='technical-rule')
router.register(r'medical-rules', MedicalRuleViewSet, basename='medical-rule')

urlpatterns = [
    path('', include(router.urls)),
]


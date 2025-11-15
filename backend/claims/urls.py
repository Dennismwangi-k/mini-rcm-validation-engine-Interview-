from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClaimViewSet, ValidationJobViewSet

router = DefaultRouter()
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'jobs', ValidationJobViewSet, basename='validationjob')

urlpatterns = [
    path('', include(router.urls)),
]


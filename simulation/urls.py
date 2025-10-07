# simulation/urls.py
# What-If Analysis and Simulation URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SimulationScenarioViewSet, SimulationRunViewSet, SimulationModelViewSet,
    SimulationResultViewSet, OptimizationTargetViewSet, SensitivityAnalysisViewSet,
    MonteCarloSimulationViewSet
)

router = DefaultRouter()
router.register(r'scenarios', SimulationScenarioViewSet)
router.register(r'runs', SimulationRunViewSet)
router.register(r'models', SimulationModelViewSet)
router.register(r'results', SimulationResultViewSet)
router.register(r'targets', OptimizationTargetViewSet)
router.register(r'sensitivity', SensitivityAnalysisViewSet)
router.register(r'monte-carlo', MonteCarloSimulationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

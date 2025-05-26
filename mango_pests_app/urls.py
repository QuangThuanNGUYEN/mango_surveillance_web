# urls.py - COMPLETE FILE WITH SURVEILLANCE CALCULATOR

from django.urls import path
from . import views
from .views import (
    HomeView, LocationListView, ThreatListView, ThreatDetailView, AboutView, 
    CompareThreatsView, CrudDashboardView, CrudRedirectView, 
    # Threat CRUD
    ThreatCreateView, ThreatUpdateView, ThreatDeleteView,
    # Location CRUD  
    LocationCreateView, LocationUpdateView, LocationDeleteView,
    # Tree CRUD
    MangoTreeCreateView, MangoTreeUpdateView, MangoTreeDeleteView,
    # AJAX API
    ThreatAjaxAPIView, ThreatAnalyticsView,
    # NEW SURVEILLANCE CALCULATOR VIEWS
    SurveillanceCalculatorView, SurveillancePlannerView, SurveillanceHistoryView,
    SurveillanceRecordCreateView, SurveillanceRecordDetailView, 
    TreeInspectionAjaxView, SurveillancePlanCreateView, SurveillanceReportView, TreeListView
)

urlpatterns = [
    # Main pages
    path('', HomeView.as_view(), name='home'),
    path('threat_list/', ThreatListView.as_view(), name='threat_list'),
    path('threat_list/<slug:threat_name>/', ThreatDetailView.as_view(), name='threat_details'),
    path('compare/', CompareThreatsView.as_view(), name='compare_threats'),
    path('about/', AboutView.as_view(), name='about'),
    path('analytics/', ThreatAnalyticsView.as_view(), name='analytics'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # SURVEILLANCE CALCULATOR - CORE BUSINESS OBJECTIVE
    path('surveillance/', SurveillanceCalculatorView.as_view(), name='surveillance_calculator'),
    path('surveillance/planner/', SurveillancePlannerView.as_view(), name='surveillance_planner'),
    path('surveillance/history/', SurveillanceHistoryView.as_view(), name='surveillance_history'),
    path('surveillance/reports/', SurveillanceReportView.as_view(), name='surveillance_reports'),
    
    # Surveillance Plans
    path('surveillance/plans/create/', SurveillancePlanCreateView.as_view(), name='surveillance_plan_create'),
    
    # Surveillance Records
    path('surveillance/records/create/', SurveillanceRecordCreateView.as_view(), name='surveillance_record_create'),
    path('surveillance/records/<int:pk>/', SurveillanceRecordDetailView.as_view(), name='surveillance_record_detail'),
    
    # Tree Inspections (AJAX)
    path('surveillance/inspections/add/', TreeInspectionAjaxView.as_view(), name='tree_inspection_add'),
    
    # CRUD Dashboard
    path('crud/', CrudDashboardView.as_view(), name='crud_dashboard'),
    path('crud/legacy/', CrudRedirectView.as_view(), name='crud'),
    
    # Traditional Threat Management (keep for fallback)
    path('threats/create/', ThreatCreateView.as_view(), name='threat_create'),
    path('threats/<slug:threat_name>/edit/', ThreatUpdateView.as_view(), name='threat_update'),
    path('threats/<slug:threat_name>/delete/', ThreatDeleteView.as_view(), name='threat_delete'),
    
    # Location Management
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', LocationUpdateView.as_view(), name='location_update'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    
    # Tree Management
    path('trees/create/', MangoTreeCreateView.as_view(), name='tree_create'),
    path('trees/<int:pk>/edit/', MangoTreeUpdateView.as_view(), name='tree_update'),
    path('trees/<int:pk>/delete/', MangoTreeDeleteView.as_view(), name='tree_delete'),
    
    # AJAX API endpoints
    path('api/threats/', ThreatAjaxAPIView.as_view(), name='api_threats'),
    path('api/threats/<int:threat_id>/', ThreatAjaxAPIView.as_view(), name='api_threat_detail'),


    path('locations/', LocationListView.as_view(), name='location_list'),
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', LocationUpdateView.as_view(), name='location_update'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    
    # Tree Management
    path('trees/', TreeListView.as_view(), name='tree_list'),
    path('trees/create/', MangoTreeCreateView.as_view(), name='tree_create'),
    path('trees/<int:pk>/edit/', MangoTreeUpdateView.as_view(), name='tree_update'),
    path('trees/<int:pk>/delete/', MangoTreeDeleteView.as_view(), name='tree_delete'),





]

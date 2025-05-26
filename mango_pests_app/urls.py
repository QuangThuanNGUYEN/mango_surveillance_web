from django.urls import path
from . import views
from .views import (
    HomeView, ThreatListView, ThreatDetailView, AboutView, 
    CompareThreatsView, CrudDashboardView, CrudRedirectView, 
    # Threat CRUD
    ThreatCreateView, ThreatUpdateView, ThreatDeleteView,
    # Location CRUD  
    LocationCreateView, LocationUpdateView, LocationDeleteView,
    # Tree CRUD
    MangoTreeCreateView, MangoTreeUpdateView, MangoTreeDeleteView,  # Added update/delete
    # API
    ThreatAPIView
)

urlpatterns = [
    # Main pages
    path('', HomeView.as_view(), name='home'),
    path('threat_list/', ThreatListView.as_view(), name='threat_list'),
    path('threat_list/<slug:threat_name>/', ThreatDetailView.as_view(), name='threat_details'),
    path('compare/', CompareThreatsView.as_view(), name='compare_threats'),
    path('about/', AboutView.as_view(), name='about'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # CRUD Dashboard
    path('crud/', CrudDashboardView.as_view(), name='crud_dashboard'),
    path('crud/legacy/', CrudRedirectView.as_view(), name='crud'),
    
    # Threat Management
    path('threats/create/', ThreatCreateView.as_view(), name='threat_create'),
    path('threats/<slug:threat_name>/edit/', ThreatUpdateView.as_view(), name='threat_update'),
    path('threats/<slug:threat_name>/delete/', ThreatDeleteView.as_view(), name='threat_delete'),
    
    # Location Management
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', LocationUpdateView.as_view(), name='location_update'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    
    # Tree Management
    path('trees/create/', MangoTreeCreateView.as_view(), name='tree_create'),
    path('trees/<int:pk>/edit/', MangoTreeUpdateView.as_view(), name='tree_update'),  # Added
    path('trees/<int:pk>/delete/', MangoTreeDeleteView.as_view(), name='tree_delete'),  # Added
    
    # API endpoints
    path('api/threats/', ThreatAPIView.as_view(), name='api_threats'),
]

from django.urls import re_path
from .views import HomeView, ThreatListView, ThreatDetailView, AboutView, CrudView, CompareThreatsView

urlpatterns = [
    re_path(r'^$', HomeView.as_view(), name='home'),
    
    re_path(r'^threat_list/$', ThreatListView.as_view(), name='threat_list'),
    
    re_path(r'^threat_list/(?P<threat_name>[\w-]+)/$', ThreatDetailView.as_view(), name='threat_details'),
    
    re_path(r'^compare/$', CompareThreatsView.as_view(), name='compare_threats'),
    
    re_path(r'^about/$', AboutView.as_view(), name='about'),
    
    re_path(r'^crud/$', CrudView.as_view(), name='crud'),
    

]

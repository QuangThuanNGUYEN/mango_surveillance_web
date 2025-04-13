from django.urls import path, re_path
from .views import HomeView, ThreatListView, ThreatDetailView, AboutView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    path('threat_list/', ThreatListView.as_view(), name='threat_list'),

    # You can keep re_path if you expect dashes or custom slugs
    re_path(r'^threat_list/(?P<threat_name>[\w-]+)/$', ThreatDetailView.as_view(), name='threat_details'),

    path('about/', AboutView.as_view(), name='about'),
]

from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('project_list/', views.project_list, name='project_list'),
    
    # path('project_list/<str:project_name>/', views.project_details, name='project_details'),
    re_path(r'^project_list/(?P<project_name>[\w-]+)/$', views.project_details, name='project_details'),

    
    path('about/', views.about, name='about'),
]
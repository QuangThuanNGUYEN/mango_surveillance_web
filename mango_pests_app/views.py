# views.py

from django.views.generic import TemplateView, View
from django.shortcuts import render
from .data import mango_threats


# Home Page
class HomeView(TemplateView):
    template_name = 'mango_pests_app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Home'
        context['heading'] = "Welcome to the World Mango Organisation of Group-28 of HIT237!"
        context['description'] = "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more about the pests that are consuming our beloved mangos!"
        return context


# Threat List Page
class ThreatListView(TemplateView):
    template_name = 'mango_pests_app/threat_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Diseases & Pests'
        context['threats'] = mango_threats
        return context


# Threat Details Page
class ThreatDetailView(View):
    def get(self, request, threat_name):
        threat = next((item for item in mango_threats if item.slug == threat_name), None)
        if threat:
            return render(request, 'mango_pests_app/threat_details.html', {'threat': threat})
        else:
            return render(request, 'mango_pests_app/404.html')


# About Page
class AboutView(TemplateView):
    template_name = 'mango_pests_app/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "About Us"
        context['team_members'] = [
            {'name': 'Mitchell Danks', 'student_id': 'S320289', 'image': 'aboutmitchell.png'},
            {'name': 'Benjamin Denison-Love', 'student_id': 'S330803', 'image': 'aboutbenjamin.png'},
            {'name': 'Quang Thuan Nguyen', 'student_id': 'S370553', 'image': 'aboutquang.png'},
            {'name': 'Spencer Siu', 'student_id': 'S344930', 'image': 'aboutspencer.png'}
        ]
        return context

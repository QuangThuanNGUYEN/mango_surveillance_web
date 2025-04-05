from django.shortcuts import render, get_object_or_404
from .data import mango_threats # lets you call the threat details inside data.py

# Home page 
def home(request):
    page_title = "home"
    homepage_content = {
        'heading': "Welcome to the World Mango Organisation of Group-28 of HIT237!",
        'description': "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more about the pests that are consuming our beloved mangos!"
    }
    return render(request, 'mango_pests_app/home.html', {'page_title': 'Home'})


# Threats List
def project_list(request):
    return render(request, 'mango_pests_app/project_list.html', {'page_title': 'Diseases & Pests', 'projects': mango_threats})


# Threat Details
def project_details(request, project_name):
    project = next((item for item in mango_threats if item.slug == project_name), None)
    if project:
        return render(request, 'mango_pests_app/project_details.html', {'project': project})
    else:
        return render(request, 'mango_pests_app/404.html')

# About
def about(request):
    page_title = "About Us"  
    team_members = [
        {'name': 'Mitchell Danks', 'student_id': 'S320289', 'image': 'aboutmitchell.png'},
        {'name': 'Benjamin Denison-Love', 'student_id': 'S330803', 'image': 'aboutbenjamin.png'},
        {'name': 'Quang Thuan Nguyen', 'student_id': 'S370553', 'image': 'aboutquang.png'},
        {'name': 'Spencer Siu', 'student_id': 'S344930', 'image': 'aboutspencer.png'}
    ]
    return render(request, 'mango_pests_app/about.html', {'page_title': page_title, 'team_members': team_members})
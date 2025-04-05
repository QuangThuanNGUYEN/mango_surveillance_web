from django.shortcuts import render, get_object_or_404
from .data import projects #lets you call the project details inside data.py

# Home page 
def home(request):
    page_title = "home"
    homepage_content = {
        'heading': "Welcome to the World Mango Organisation!",
        'description': "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more!"
    }
    return render(request, 'mango_pests_app/home.html', {'page_title': 'Home'})

# Project Welcome



# Project List
# def project_list(request):
#     projects = [
#         {'name': 'Anthracnose', 'description': 'Description of Project 1', 'image': 'Anthracnose.png', 'details': 'Full details of Anthracnose'},
#         {'name': 'Bacterial Black Spot', 'description': 'Description of Project 2', 'image': 'bacterialblackspot.png', 'details': 'Full details of Bacterial Black Spot'},
#         {'name': 'Mango Scab', 'description': 'Description of Project 3', 'image': 'mangoscab.png', 'details': 'Full details of Mango Scab'},
#         {'name': 'Mango Scale', 'description': 'Description of Project 4', 'image': 'mangoscale.png', 'details': 'Full details of Mango Scale'},
#         {'name': 'Fruit Fly', 'description': 'Description of Project 5', 'image': 'fruitfly.png', 'details': 'Full details of Fruit Fly'},
#         {'name': 'Mango Leafhoppers', 'description': 'Description of Project 6', 'image': 'mangoleafhopper.png', 'details': 'Full details of Mango Leafhoppers'},
#         {'name': 'Mango Seed Weevil', 'description': 'Description of Project 7', 'image': 'seedweevil.png', 'details': 'Full details of Mango Seed Weevil'},
#     ]
#     return render(request, 'mango_pests_app/project_list.html', {'page_title': 'Diseases & Pests', 'projects': projects})

def project_list(request):
    return render(request, 'mango_pests_app/project_list.html', {'page_title': 'Diseases & Pests', 'projects': projects})

# Project Details 
# def project_details(request, project_name):
#     projects = [
#         {'name': 'Anthracnose', 'description': 'Description of Project 1', 'image': 'Anthracnose.png', 'details': 'Full details of Anthracnose'},
#         {'name': 'Bacterial Black Spot', 'description': 'Description of Project 2', 'image': 'bacterialblackspot.png', 'details': 'Full details of Bacterial Black Spot'},
#         {'name': 'Mango Scab', 'description': 'Description of Project 3', 'image': 'mangoscab.png', 'details': 'Full details of Mango Scab'},
#         {'name': 'Mango Scale', 'description': 'Description of Project 4', 'image': 'mangoscale.png', 'details': 'Full details of Mango Scale'},
#         {'name': 'Fruit Fly', 'description': 'Description of Project 5', 'image': 'fruitfly.png', 'details': 'Full details of Fruit Fly'},
#         {'name': 'Mango Leafhoppers', 'description': 'Description of Project 6', 'image': 'mangoleafhopper.png', 'details': 'Full details of Mango Leafhoppers'},
#         {'name': 'Mango Seed Weevil', 'description': 'Description of Project 7', 'image': 'seedweevil.png', 'details': 'Full details of Mango Seed Weevil'},
#     ]
#     project = next((item for item in projects if item['name'].lower() == project_name.lower()), None)
#     return render(request, 'mango_pests_app/project_details.html', {'project': project})

def project_details(request, project_name):
    project = next((item for item in projects if item['slug'] == project_name), None)
    return render(request, 'mango_pests_app/project_details.html', {'project': project})

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
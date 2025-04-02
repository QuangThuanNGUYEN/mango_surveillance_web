from django.shortcuts import render

def home(request):
    return render(request, 'mango_pests_app/home.html', {'page_title': 'Home'})

def project_list(request):
    projects = [
        {'name': 'Project 1', 'description': 'Description of Project 1', 'image': 'mangodp1.png'},
        {'name': 'Project 2', 'description': 'Description of Project 2', 'image': 'mangodp2.png'},
        {'name': 'Project 3', 'description': 'Description of Project 3', 'image': 'mangodp3.png'},
        {'name': 'Project 4', 'description': 'Description of Project 4', 'image': 'mangodp4.png'},
        {'name': 'Project 5', 'description': 'Description of Project 5', 'image': 'mangodp5.png'},
        {'name': 'Project 6', 'description': 'Description of Project 6', 'image': 'mangodp6.png'},
        {'name': 'Project 7', 'description': 'Description of Project 7', 'image': 'mangodp7.png'},
    ]
    return render(request, 'mango_pests_app/project_list.html', {'page_title': 'Diseases & Pests', 'projects': projects})

def about(request):
    page_title = "About Us"  
    team_members = [
        {'name': 'Mitchell Danks', 'student_id': 'S320289', 'image': 'aboutmitchell.png'},
        {'name': 'Benjamin Denison-Love', 'student_id': 'S330803', 'image': 'aboutbenjamin.png'},
        {'name': 'Quang Thuan Nguyen', 'student_id': 'S370553', 'image': 'aboutquang.png'},
        {'name': 'Spencer Siu', 'student_id': 'S344930', 'image': 'aboutspencer.png'}
    ]
    return render(request, 'mango_pests_app/about.html', {'page_title': page_title, 'team_members': team_members})
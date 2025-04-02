from django.shortcuts import render

def home(request):
    return render(request, 'mango_pests_app/home.html', {'page_title': 'Home'})

def project_list(request):
    projects = [
        {'name': 'Anthracnose', 'description': 'Description of Project 1', 'image': 'Anthracnose.png'},
        {'name': 'Bacterial Black Spot', 'description': 'Description of Project 2', 'image': 'bacterialblackspot.png'},
        {'name': 'Mango Scab', 'description': 'Description of Project 3', 'image': 'mangoscab.png'},
        {'name': 'Mango Scale', 'description': 'Description of Project 4', 'image': 'mangoscale.png'},
        {'name': 'Fruit Fly', 'description': 'Description of Project 5', 'image': 'fruitfly.png'},
        {'name': 'Mango Leafhoppers', 'description': 'Description of Project 6', 'image': 'mangoleafhopper.png'},
        {'name': 'Mango Seed Weevil', 'description': 'Description of Project 7', 'image': 'seedweevil.png'},
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
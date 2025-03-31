from django.shortcuts import render

def home(request):
    return render(request, 'mango_pests_app/home.html', {'page_title': 'Home'})

def project_list(request):
    return render(request, 'mango_pests_app/project_list.html', {'page_title': 'Diseases & Pests'})

def about(request):
    return render(request, 'mango_pests_app/about.html', {'page_title': 'About Us'})
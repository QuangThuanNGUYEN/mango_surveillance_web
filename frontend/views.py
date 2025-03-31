from django.shortcuts import render

def home(request):
    return render(request, 'frontend/home.html')

def project_list(request):
    return render(request, 'frontend/project_list.html')

def project_details(request):
    return render(request, 'frontend/project_details.html')

def about(request):
    return render(request, 'frontend/about.html')
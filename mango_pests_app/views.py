from django.shortcuts import render

def home(request):
    return render(request, 'mango_pests_app/home.html')

def project_list(request):
    return render(request, 'mango_pests_app/project_list.html')

def project_details(request):
    return render(request, 'mango_pests_app/project_details.html')

def about(request):
    return render(request, 'mango_pests_app/about.html')
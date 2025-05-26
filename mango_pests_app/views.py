# views.py
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import render, redirect
from .models import MangoThreat, Location, MangoTree, SurveillanceRecord, Grower
from .forms import (
    MangoThreatForm, LocationForm, MangoTreeForm, UserRegistrationForm
)
from .models import MangoThreat, Location, MangoTree, Grower
from django.db.models import Q  
from .data import mango_threats  

# Home Page
class HomeView(TemplateView):
    """
    View for the home page of the Mango Pests & Diseases website.
    """
    template_name = 'mango_pests_app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = "Welcome to the World Mango Organisation of Group 28 of HIT237!"
        context['description'] = "We are dedicated to combating mango pests and diseases through research and awareness. Browse our site to learn more about the threats affecting our beloved mangos!"
        
        # Add some statistics
        context['total_threats'] = MangoThreat.objects.count()
        context['pest_count'] = MangoThreat.objects.filter(threat_type='pest').count()
        context['disease_count'] = MangoThreat.objects.filter(threat_type='disease').count()
        
        return context


class ThreatListView(TemplateView):
    template_name = 'mango_pests_app/threat_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # === Initial data ===
        threats = mango_threats

        # === Search ===
        query = self.request.GET.get('q', '').strip().lower()
        if query:
            threats = [
                t for t in threats
                if query in t.name.lower() or query in t.description.lower()
            ]

        # === Category filter ===
        category = self.request.GET.get('category', '')
        if category in ['pest', 'disease']:
            threats = [t for t in threats if t.threat_type == category]

        # === Sort ===
        sort_option = self.request.GET.get('sort', 'name_asc')
        if sort_option == 'name_desc':
            threats.sort(key=lambda t: t.name, reverse=True)
        else:
            threats.sort(key=lambda t: t.name)

        # === Pagination ===
        paginator = Paginator(threats, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # === Count info ===
        pest_count = len([t for t in threats if t.threat_type == 'pest'])
        disease_count = len([t for t in threats if t.threat_type == 'disease'])

        # === Context ===
        context.update({
            'page_obj': page_obj,
            'query': query,
            'threat_type': category,
            'sort_option': sort_option,
            'pest_count': pest_count,
            'disease_count': disease_count,
            'total_results': len(threats),
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
        })

        return context

# Threat Detail Page
class ThreatDetailView(DetailView):
    """
    DetailView for displaying individual threat information.
    """
    model = MangoThreat
    template_name = 'mango_pests_app/threat_details.html'
    context_object_name = 'threat'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'


# Compare Threats Page
class CompareThreatsView(FormView):
    """
    Enhanced view to compare selected mango threats.
    """
    template_name = 'mango_pests_app/compare_threats.html'
    MAX_SELECTIONS = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['threats'] = MangoThreat.objects.all().order_by('name')
        return context

    def post(self, request, *args, **kwargs):
        selected_slugs = request.POST.getlist('threats')

        if len(selected_slugs) == 0:
            messages.error(request, "Please select at least one threat to compare.")
            return self.get(request, *args, **kwargs)

        if len(selected_slugs) > self.MAX_SELECTIONS:
            messages.error(request, f"You can only compare up to {self.MAX_SELECTIONS} threats.")
            return self.get(request, *args, **kwargs)

        selected_threats = MangoThreat.objects.filter(slug__in=selected_slugs)
        
        context = self.get_context_data()
        context['selected_threats'] = selected_threats
        
        return render(request, self.template_name, context)


# CRUD Views for MangoThreat
class ThreatCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new mango threat.
    """
    model = MangoThreat
    form_class = MangoThreatForm
    template_name = 'mango_pests_app/crud/threat_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'Threat "{form.instance.name}" has been created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('crud_dashboard')


class ThreatUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing mango threat.
    """
    model = MangoThreat
    form_class = MangoThreatForm
    template_name = 'mango_pests_app/crud/threat_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'
    
    def form_valid(self, form):
        messages.success(self.request, f'Threat "{form.instance.name}" has been updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('crud_dashboard')


class ThreatDeleteView(LoginRequiredMixin, DeleteView):
    """
    Delete a mango threat.
    """
    model = MangoThreat
    template_name = 'mango_pests_app/crud/threat_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'
    success_url = reverse_lazy('crud_dashboard')
    
    def delete(self, request, *args, **kwargs):
        threat = self.get_object()
        messages.success(request, f'Threat "{threat.name}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)



# Location CRUD Views
class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'mango_pests_app/crud/location_list.html'
    context_object_name = 'locations'
    paginate_by = 10


class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'mango_pests_app/crud/location_form.html'
    success_url = reverse_lazy('location_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Location "{form.instance.name}" has been created!')
        return super().form_valid(form)


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'mango_pests_app/crud/location_form.html'
    success_url = reverse_lazy('location_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Location "{form.instance.name}" has been updated!')
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, DeleteView):
    model = Location
    template_name = 'mango_pests_app/crud/location_confirm_delete.html'
    success_url = reverse_lazy('location_list')
    
    def delete(self, request, *args, **kwargs):
        location = self.get_object()
        messages.success(request, f'Location "{location.name}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)

# MangoTree CRUD Views
class MangoTreeListView(LoginRequiredMixin, ListView):
    model = MangoTree
    template_name = 'mango_pests_app/crud/tree_list.html'
    context_object_name = 'trees'
    paginate_by = 15


class MangoTreeCreateView(LoginRequiredMixin, CreateView):
    model = MangoTree
    form_class = MangoTreeForm
    template_name = 'mango_pests_app/crud/tree_form.html'
    success_url = reverse_lazy('tree_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Tree "{form.instance.tree_id}" has been created!')
        return super().form_valid(form)
    
class MangoTreeUpdateView(LoginRequiredMixin, UpdateView):
    model = MangoTree
    form_class = MangoTreeForm
    template_name = 'mango_pests_app/crud/tree_form.html'
    success_url = reverse_lazy('crud_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Tree "{form.instance.tree_id}" has been updated!')
        return super().form_valid(form)


class MangoTreeDeleteView(LoginRequiredMixin, DeleteView):
    model = MangoTree
    template_name = 'mango_pests_app/crud/tree_confirm_delete.html'
    success_url = reverse_lazy('crud_dashboard')
    
    def delete(self, request, *args, **kwargs):
        tree = self.get_object()
        messages.success(request, f'Tree "{tree.tree_id}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)
    
# --- CRUD Dashboard ---
class CrudDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/crud_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_threats'] = MangoThreat.objects.order_by('-created_at')[:5]
        context['recent_locations'] = Location.objects.all()[:5]
        context['recent_trees'] = MangoTree.objects.order_by('-id')[:5]
        
        context['stats'] = {
            'total_threats': MangoThreat.objects.count(),
            'total_pests': MangoThreat.objects.filter(threat_type='pest').count(),
            'total_diseases': MangoThreat.objects.filter(threat_type='disease').count(),
            'total_locations': Location.objects.count(),
            'total_trees': MangoTree.objects.count(),
        }
        return context

# About Page (unchanged)
class AboutView(TemplateView):
    """
    View for the About Us page.
    """
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


# API Views for AJAX operations
class ThreatAPIView(LoginRequiredMixin, TemplateView):
    """
    API endpoint for threat operations via AJAX.
    """
    
    def get(self, request, *args, **kwargs):
        """Return threat data as JSON."""
        threats = MangoThreat.objects.all()
        data = [{
            'id': threat.id,
            'name': threat.name,
            'slug': threat.slug,
            'threat_type': threat.threat_type,
            'risk_level': threat.risk_level,
        } for threat in threats]
        
        return JsonResponse({'threats': data})


# Legacy CRUD View (keeping for backward compatibility)
class CrudView(LoginRequiredMixin, TemplateView):
    """
    Legacy CRUD view - now redirects to new dashboard.
    """
    def get(self, request, *args, **kwargs):
        return redirect('crud_dashboard')
    
    #Login Page
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'mango_pests_app/login.html')

#Register Page
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'mango_pests_app/register.html', {'form': form})

#Logout View
def logout_view(request):
    logout(request)
    return redirect('home') 

class CrudRedirectView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get current user's grower record
        grower = Grower.objects.filter(user=self.request.user).first()

        locations = Location.objects.all()
        mango_trees = MangoTree.objects.all()

        context['grower'] = grower
        context['locations'] = locations
        context['mango_trees'] = mango_trees
        return context
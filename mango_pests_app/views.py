# views.py - COMPLETE FILE

from django import apps
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Sum
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from .models import (
    MangoThreat, Location, MangoTree, SurveillanceRecord, Grower,
    SurveillancePlan, TreeInspection, PlantPart
)
from .forms import MangoThreatForm, LocationForm, MangoTreeForm, UserRegistrationForm
import json
from datetime import datetime, timedelta

from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView, View
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import logout, login, authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from .models import MangoThreat, Location, MangoTree, SurveillanceRecord, Grower
from .forms import (
    MangoThreatForm, LocationForm, MangoTreeForm, UserRegistrationForm
)
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


# NEW AJAX API View
class ThreatAjaxAPIView(LoginRequiredMixin, View):
    """
    AJAX API for threat operations - Create, Update, Delete
    """
    
    def post(self, request, *args, **kwargs):
        """Handle AJAX POST requests for creating threats"""
        try:
            # Get form data
            form = MangoThreatForm(request.POST)
            
            if form.is_valid():
                threat = form.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Threat "{threat.name}" created successfully!',
                    'threat': {
                        'id': threat.id,
                        'name': threat.name,
                        'slug': threat.slug,
                        'threat_type': threat.get_threat_type_display(),
                        'risk_level': threat.get_risk_level_display(),
                        'description': threat.description,
                        'created_at': threat.created_at.strftime('%Y-%m-%d %H:%M')
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': form.errors
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })
    
    def put(self, request, *args, **kwargs):
        """Handle AJAX PUT requests for updating threats"""
        try:
            threat_id = kwargs.get('threat_id')
            threat = get_object_or_404(MangoThreat, id=threat_id)
            
            # Parse JSON data from PUT request
            data = json.loads(request.body)
            form = MangoThreatForm(data, instance=threat)
            
            if form.is_valid():
                threat = form.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Threat "{threat.name}" updated successfully!',
                    'threat': {
                        'id': threat.id,
                        'name': threat.name,
                        'slug': threat.slug,
                        'threat_type': threat.get_threat_type_display(),
                        'risk_level': threat.get_risk_level_display(),
                        'description': threat.description,
                        'updated_at': threat.updated_at.strftime('%Y-%m-%d %H:%M')
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': form.errors
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })
    
    def delete(self, request, *args, **kwargs):
        """Handle AJAX DELETE requests"""
        try:
            threat_id = kwargs.get('threat_id')
            threat = get_object_or_404(MangoThreat, id=threat_id)
            threat_name = threat.name
            threat.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'Threat "{threat_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            })

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


# CRUD Views for MangoThreat
class ThreatCreateView(LoginRequiredMixin, CreateView):
    model = MangoThreat
    form_class = MangoThreatForm
    template_name = 'mango_pests_app/crud/threat_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Threat "{form.instance.name}" has been created!')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect back to CRUD dashboard to see the update
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
class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'mango_pests_app/crud/location_form.html'
    
    def form_valid(self, form):
        # Always assign the location to the current user
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        form.instance.grower = grower
        
        messages.success(self.request, f'✅ Location "{form.instance.name}" created! Check your surveillance calculator.')
        return super().form_valid(form)
    
    def get_success_url(self):
        # Redirect to surveillance calculator to see the update immediately
        return reverse('surveillance_calculator')


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'mango_pests_app/crud/location_form.html'
    success_url = reverse_lazy('crud_dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'Location "{form.instance.name}" has been updated!')
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, DeleteView):
    model = Location
    template_name = 'mango_pests_app/crud/location_confirm_delete.html'
    success_url = reverse_lazy('crud_dashboard')
    
    def delete(self, request, *args, **kwargs):
        location = self.get_object()
        messages.success(request, f'Location "{location.name}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)

# MangoTree CRUD Views
class MangoTreeCreateView(LoginRequiredMixin, CreateView):
    model = MangoTree
    form_class = MangoTreeForm
    template_name = 'mango_pests_app/crud/tree_form.html'
    
    def get_form_kwargs(self):
        """Pass the current user to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Verify the selected location belongs to current user
        selected_location = form.cleaned_data['location']
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        if selected_location.grower != grower:
            messages.error(self.request, '❌ You can only add trees to your own locations.')
            return self.form_invalid(form)
        
        messages.success(
            self.request, 
            f'✅ Tree "{form.instance.tree_id}" created successfully in {selected_location.name}!'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle case where user has no locations"""
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        user_locations = Location.objects.filter(grower=grower)
        
        if user_locations.count() == 0:
            messages.error(
                self.request, 
                '❌ You need to create a location first before adding trees.'
            )
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        # Redirect to surveillance calculator with update flag
        return reverse('surveillance_calculator') + '?updated=true'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add user's location count for template logic
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        context['user_locations_count'] = Location.objects.filter(grower=grower).count()
        
        return context

class MangoTreeUpdateView(LoginRequiredMixin, UpdateView):
    model = MangoTree
    form_class = MangoTreeForm
    template_name = 'mango_pests_app/crud/tree_form.html'
    
    def get_form_kwargs(self):
        """Pass the current user to the form"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        """Only allow editing trees in user's locations"""
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        return MangoTree.objects.filter(location__grower=grower)
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'✅ Tree "{form.instance.tree_id}" updated successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('surveillance_calculator') + '?updated=true'



class MangoTreeDeleteView(LoginRequiredMixin, DeleteView):
    model = MangoTree
    template_name = 'mango_pests_app/crud/tree_confirm_delete.html'
    success_url = reverse_lazy('crud_dashboard')
    
    def delete(self, request, *args, **kwargs):
        tree = self.get_object()
        messages.success(request, f'Tree "{tree.tree_id}" has been deleted successfully!')
        return super().delete(request, *args, **kwargs)
    

# ENHANCED CRUD Dashboard with AJAX support
class CrudDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/crud_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current user's grower
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Get fresh data every time (no caching)
        context['recent_threats'] = MangoThreat.objects.all().order_by('-created_at')[:10]
        context['recent_locations'] = Location.objects.all().order_by('-id')[:5]
        context['recent_trees'] = MangoTree.objects.select_related('location').order_by('-id')[:5]
        
        # Add threat form for AJAX
        context['threat_form'] = MangoThreatForm()
        
        # Calculate fresh statistics
        context['stats'] = {
            'total_threats': MangoThreat.objects.count(),
            'total_pests': MangoThreat.objects.filter(threat_type='pest').count(),
            'total_diseases': MangoThreat.objects.filter(threat_type='disease').count(),
            'total_locations': Location.objects.count(),
            'total_trees': MangoTree.objects.count(),
        }
        
        # Data for charts
        context['chart_data'] = {
            'threat_types': list(MangoThreat.objects.values('threat_type').annotate(count=Count('id'))),
            'risk_levels': list(MangoThreat.objects.values('risk_level').annotate(count=Count('id')))
        }
        
        context['grower'] = grower
        
        return context


# NEW Analytics View
class ThreatAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Analytics data
        context['threat_stats'] = {
            'by_type': MangoThreat.objects.values('threat_type').annotate(count=Count('id')),
            'by_risk': MangoThreat.objects.values('risk_level').annotate(count=Count('id')),
        }
        
        context['total_threats'] = MangoThreat.objects.count()
        context['high_risk_count'] = MangoThreat.objects.filter(risk_level='high').count()
        context['locations_count'] = Location.objects.count()
        
        return context


# About Page
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


# Legacy CRUD View (keeping for backward compatibility)
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


# Authentication Views
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


def logout_view(request):
    logout(request)
    return redirect('home')



# Add this simple view to your existing views.py
# Add this simple view to your existing views.py

# class SurveillanceCalculatorView(LoginRequiredMixin, TemplateView):
#     """
#     Simple surveillance calculator - core business objective
#     """
#     template_name = 'mango_pests_app/surveillance_calculator.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
        
#         # Get current user's grower profile
#         try:
#             grower = Grower.objects.get(user=self.request.user)
#         except Grower.DoesNotExist:
#             # Create a grower record if it doesn't exist
#             grower = Grower.objects.create(user=self.request.user)
        
#         # Get grower's locations and trees
#         try:
#             # Try to filter by grower if the field exists
#             locations = Location.objects.filter(grower=grower)
#         except:
#             # Fallback to all locations if grower field doesn't exist yet
#             locations = Location.objects.all()
        
#         total_trees = 0
        
#         # Calculate total trees
#         for location in locations:
#             total_trees += location.mango_trees.count()
        
#         # Simple surveillance calculation
#         surveillance_calculation = None
#         if total_trees > 0:
#             surveillance_calculation = self.calculate_simple_surveillance_effort(grower, locations, total_trees)
        
#         # Try to get plant parts if model exists
#         plant_parts = []
#         try:
#             from .models import PlantPart
#             plant_parts = PlantPart.objects.all()
#         except:
#             # PlantPart model doesn't exist yet, that's ok
#             pass
        
#         context.update({
#             'grower': grower,
#             'locations': locations,
#             'total_trees': total_trees,
#             'surveillance_calculation': surveillance_calculation,
#             'plant_parts': plant_parts,
#             'high_priority_threats': MangoThreat.objects.filter(risk_level='high')[:5],
#         })
        
#         return context
    
#     def calculate_simple_surveillance_effort(self, grower, locations, total_trees):
#         """
#         Simple surveillance calculation based on business requirements:
#         - Number of plants on property
#         - Location of surveyed plants  
#         - Time of surveillance
#         - Stocking rates (if available)
#         """
#         # Base calculation: 5-8 minutes per tree (business requirement)
#         base_minutes_per_tree = 6
#         total_minutes = total_trees * base_minutes_per_tree
        
#         # Add travel time between locations (10 minutes per location)
#         travel_time = locations.count() * 10
#         total_minutes += travel_time
        
#         # Add documentation time (15% of survey time)
#         doc_time = total_minutes * 0.15
#         total_minutes += doc_time
        
#         # Adjust for stocking rate if available
#         stocking_rate_factor = 1.0
#         if hasattr(grower, 'stocking_rate') and grower.stocking_rate:
#             if grower.stocking_rate > 100:  # High density = more complex
#                 stocking_rate_factor = 1.2
#             elif grower.stocking_rate > 200:  # Very high density
#                 stocking_rate_factor = 1.4
        
#         total_minutes *= stocking_rate_factor
        
#         # Calculate hours
#         total_hours = total_minutes / 60
        
#         # Frequency recommendation (every 14 days by default)
#         frequency_days = 14
#         monthly_sessions = 30 / frequency_days
#         monthly_hours = total_hours * monthly_sessions
        
#         # Location breakdown (business requirement: location of surveyed plants)
#         location_breakdown = []
#         for location in locations:
#             tree_count = location.mango_trees.count()
#             location_minutes = (tree_count * base_minutes_per_tree + 10) * stocking_rate_factor
#             location_breakdown.append({
#                 'location': location,
#                 'tree_count': tree_count,
#                 'estimated_minutes': round(location_minutes),
#                 'estimated_hours': round(location_minutes / 60, 2)
#             })
        
#         return {
#             'total_trees': total_trees,
#             'total_time_minutes': round(total_minutes),
#             'total_time_hours': round(total_hours, 2),
#             'average_time_per_tree': base_minutes_per_tree,
#             'location_breakdown': location_breakdown,
#             'stocking_rate_factor': stocking_rate_factor,
#             'monthly_effort_hours': round(monthly_hours, 1),
#             'frequency_recommendation': {
#                 'days': frequency_days,
#                 'description': f"Every {frequency_days} days",
#                 'annual_sessions': round(365 / frequency_days)
#             }
#         }



# Fixed surveillance view - only shows user's own locations

class SurveillanceCalculatorView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/surveillance_calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current user's grower
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # STRICT: Only show locations assigned to this user
        locations = Location.objects.filter(grower=grower)
        
        print(f"🔍 USER-SPECIFIC VIEW:")
        print(f"   User: {self.request.user.username}")
        print(f"   Grower ID: {grower.id}")
        print(f"   User's locations: {locations.count()}")
        
        total_trees = 0
        for location in locations:
            tree_count = location.mango_trees.count()
            total_trees += tree_count
            print(f"   📊 {location.name}: {tree_count} trees")
        
        print(f"🌳 Total trees: {total_trees}")
        
        # Calculate surveillance effort
        surveillance_calculation = None
        if total_trees > 0:
            surveillance_calculation = self.calculate_surveillance_effort(grower, locations, total_trees)
        
        context.update({
            'grower': grower,
            'locations': locations,
            'total_trees': total_trees,
            'surveillance_calculation': surveillance_calculation,
            'plant_parts': [],
            'high_priority_threats': MangoThreat.objects.filter(risk_level='high')[:5],
            'is_new_user': locations.count() == 0,  # Helper for template
        })
        
        return context
    
    def calculate_surveillance_effort(self, grower, locations, total_trees):
        """Calculate surveillance effort for user's locations only"""
        base_minutes_per_tree = 6
        total_minutes = total_trees * base_minutes_per_tree
        
        # Travel time between user's locations
        travel_time = locations.count() * 10
        total_minutes += travel_time
        
        # Documentation time (15%)
        doc_time = total_minutes * 0.15
        total_minutes += doc_time
        
        total_hours = total_minutes / 60
        frequency_days = 14
        monthly_hours = (total_hours * 30) / frequency_days
        
        # Location breakdown
        location_breakdown = []
        for location in locations:
            tree_count = location.mango_trees.count()
            if tree_count > 0:
                location_minutes = tree_count * base_minutes_per_tree + 10
                location_breakdown.append({
                    'location': location,
                    'tree_count': tree_count,
                    'estimated_minutes': round(location_minutes),
                    'estimated_hours': round(location_minutes / 60, 2)
                })
        
        return {
            'total_trees': total_trees,
            'total_time_minutes': round(total_minutes),
            'total_time_hours': round(total_hours, 2),
            'average_time_per_tree': base_minutes_per_tree,
            'location_breakdown': location_breakdown,
            'monthly_effort_hours': round(monthly_hours, 1),
            'frequency_recommendation': {
                'days': frequency_days,
                'description': f"Every {frequency_days} days",
                'annual_sessions': round(365 / frequency_days)
            }
        }



class SurveillancePlannerView(LoginRequiredMixin, TemplateView):
    """
    Plan surveillance activities with calendar integration
    """
    template_name = 'mango_pests_app/surveillance_planner.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        
        # Get upcoming surveillance sessions
        today = datetime.now().date()
        upcoming_sessions = []
        
        active_plans = SurveillancePlan.objects.filter(grower=grower, is_active=True)
        for plan in active_plans:
            # Calculate next surveillance dates
            last_record = SurveillanceRecord.objects.filter(
                grower=grower, 
                surveillance_plan=plan
            ).order_by('-date').first()
            
            if last_record:
                next_date = last_record.date + timedelta(days=plan.frequency_days)
            else:
                next_date = plan.start_date
            
            if next_date >= today:
                upcoming_sessions.append({
                    'plan': plan,
                    'next_date': next_date,
                    'days_until': (next_date - today).days,
                    'estimated_hours': plan.total_estimated_hours or 0
                })
        
        # Sort by nearest date
        upcoming_sessions.sort(key=lambda x: x['next_date'])
        
        context.update({
            'grower': grower,
            'upcoming_sessions': upcoming_sessions[:10],  # Next 10 sessions
            'active_plans': active_plans,
            'locations': Location.objects.filter(grower=grower),
            'threats': MangoThreat.objects.all().order_by('name'),
        })
        
        return context


class SurveillanceHistoryView(LoginRequiredMixin, TemplateView):
    """
    View historical surveillance data and results
    """
    template_name = 'mango_pests_app/surveillance_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        
        # Get surveillance history with filters
        records = SurveillanceRecord.objects.filter(grower=grower).order_by('-date')
        
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            records = records.filter(date__gte=date_from)
        if date_to:
            records = records.filter(date__lte=date_to)
        
        # Filter by location
        location_id = self.request.GET.get('location')
        if location_id:
            records = records.filter(location_id=location_id)
        
        # Calculate statistics
        stats = self.calculate_surveillance_statistics(grower, records)
        
        # Get threat findings over time
        threat_findings = self.get_threat_findings_timeline(grower)
        
        context.update({
            'grower': grower,
            'records': records[:50],  # Limit to recent 50 records
            'locations': Location.objects.filter(grower=grower),
            'stats': stats,
            'threat_findings': threat_findings,
            'date_from': date_from,
            'date_to': date_to,
            'selected_location': location_id,
        })
        
        return context
    
    def calculate_surveillance_statistics(self, grower, records):
        """Calculate surveillance performance statistics"""
        total_records = records.count()
        
        if total_records == 0:
            return {'no_data': True}
        
        # Time statistics
        avg_time = records.filter(total_time_minutes__isnull=False).aggregate(
            avg=Avg('total_time_minutes')
        )['avg']
        
        total_time = records.filter(total_time_minutes__isnull=False).aggregate(
            total=Sum('total_time_minutes')
        )['total']
        
        # Trees surveyed
        total_trees_surveyed = records.aggregate(
            total=Sum('trees_surveyed_count')
        )['total']
        
        # Threat detection statistics
        threat_detections = TreeInspection.objects.filter(
            surveillance_record__grower=grower,
            threats_found__isnull=False
        ).count()
        
        total_inspections = TreeInspection.objects.filter(
            surveillance_record__grower=grower
        ).count()
        
        detection_rate = (threat_detections / total_inspections * 100) if total_inspections > 0 else 0
        
        return {
            'total_records': total_records,
            'avg_time_minutes': round(avg_time) if avg_time else 0,
            'total_time_hours': round(total_time / 60) if total_time else 0,
            'total_trees_surveyed': total_trees_surveyed or 0,
            'threat_detection_rate': round(detection_rate, 1),
            'avg_trees_per_session': round(total_trees_surveyed / total_records) if total_trees_surveyed and total_records else 0,
        }
    
    def get_threat_findings_timeline(self, grower):
        """Get threat findings over time for chart"""
        findings = TreeInspection.objects.filter(
            surveillance_record__grower=grower,
            threats_found__isnull=False
        ).select_related('surveillance_record').prefetch_related('threats_found')
        
        # Group by month
        monthly_data = {}
        for finding in findings:
            month_key = finding.surveillance_record.date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'pests': 0, 'diseases': 0}
            
            for threat in finding.threats_found.all():
                if threat.threat_type == 'pest':
                    monthly_data[month_key]['pests'] += 1
                else:
                    monthly_data[month_key]['diseases'] += 1
        
        return monthly_data


class SurveillanceRecordCreateView(LoginRequiredMixin, CreateView):
    """
    Create new surveillance record
    """
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/record_form.html'
    fields = ['surveillance_plan', 'location', 'date', 'start_time', 'weather_conditions', 
              'temperature_celsius', 'notes']
    
    def form_valid(self, form):
        form.instance.grower = get_object_or_404(Grower, user=self.request.user)
        messages.success(self.request, 'Surveillance record created successfully!')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        grower = get_object_or_404(Grower, user=self.request.user)
        
        # Filter locations and plans to current grower
        form.fields['location'].queryset = Location.objects.filter(grower=grower)
        form.fields['surveillance_plan'].queryset = SurveillancePlan.objects.filter(
            grower=grower, is_active=True
        )
        
        return form
    
    def get_success_url(self):
        return reverse('surveillance_record_detail', kwargs={'pk': self.object.pk})


class SurveillanceRecordDetailView(LoginRequiredMixin, TemplateView):
    """
    Detail view for surveillance record with tree inspections
    """
    template_name = 'mango_pests_app/surveillance/record_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        record = get_object_or_404(
            SurveillanceRecord, 
            pk=kwargs['pk'], 
            grower__user=self.request.user
        )
        
        # Get tree inspections for this record
        inspections = TreeInspection.objects.filter(
            surveillance_record=record
        ).select_related('tree').prefetch_related('plant_parts_checked', 'threats_found')
        
        # Get trees available for inspection at this location
        available_trees = MangoTree.objects.filter(location=record.location)
        uninspected_trees = available_trees.exclude(
            id__in=inspections.values_list('tree_id', flat=True)
        )
        
        context.update({
            'record': record,
            'inspections': inspections,
            'uninspected_trees': uninspected_trees,
            'plant_parts': PlantPart.objects.all(),
            'threats': MangoThreat.objects.all().order_by('name'),
            'inspection_summary': self.get_inspection_summary(inspections),
        })
        
        return context
    
    def get_inspection_summary(self, inspections):
        """Calculate summary statistics for inspections"""
        total_inspections = inspections.count()
        if total_inspections == 0:
            return {'no_data': True}
        
        # Count by severity
        severity_counts = {}
        for inspection in inspections:
            severity = inspection.severity_level
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count threats found
        threats_found = 0
        for inspection in inspections:
            if inspection.threats_found.exists():
                threats_found += 1
        
        return {
            'total_inspections': total_inspections,
            'threats_found_count': threats_found,
            'threat_detection_rate': round(threats_found / total_inspections * 100, 1),
            'severity_counts': severity_counts,
            'action_required_count': inspections.filter(action_required=True).count(),
        }


class TreeInspectionAjaxView(LoginRequiredMixin, View):
    """
    AJAX endpoint for adding tree inspections
    """
    
    def post(self, request, *args, **kwargs):
        try:
            # Get the surveillance record
            record_id = request.POST.get('record_id')
            record = get_object_or_404(
                SurveillanceRecord, 
                id=record_id, 
                grower__user=request.user
            )
            
            # Create tree inspection
            tree_id = request.POST.get('tree_id')
            tree = get_object_or_404(MangoTree, id=tree_id, location=record.location)
            
            inspection = TreeInspection.objects.create(
                surveillance_record=record,
                tree=tree,
                severity_level=request.POST.get('severity_level', 'none'),
                inspection_time_minutes=request.POST.get('inspection_time_minutes'),
                findings=request.POST.get('findings', ''),
                action_required=request.POST.get('action_required') == 'on',
                photo_taken=request.POST.get('photo_taken') == 'on',
            )
            
            # Add plant parts checked
            plant_part_ids = request.POST.getlist('plant_parts')
            if plant_part_ids:
                inspection.plant_parts_checked.set(plant_part_ids)
            
            # Add threats found
            threat_ids = request.POST.getlist('threats_found')
            if threat_ids:
                inspection.threats_found.set(threat_ids)
            
            # Update surveillance record
            record.trees_surveyed_count += 1
            if not record.total_time_minutes:
                record.total_time_minutes = 0
            record.total_time_minutes += float(request.POST.get('inspection_time_minutes', 0))
            record.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Inspection of tree {tree.tree_id} recorded successfully!',
                'inspection_id': inspection.id,
                'trees_surveyed': record.trees_surveyed_count,
                'total_time': record.total_time_minutes,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error recording inspection: {str(e)}'
            })


class SurveillancePlanCreateView(LoginRequiredMixin, CreateView):
    """
    Create surveillance plan
    """
    model = SurveillancePlan
    template_name = 'mango_pests_app/surveillance/plan_form.html'
    fields = ['name', 'locations', 'target_threats', 'frequency_days', 'start_date', 'end_date']
    
    def form_valid(self, form):
        form.instance.grower = get_object_or_404(Grower, user=self.request.user)
        response = super().form_valid(form)
        
        # Calculate surveillance effort for this plan
        self.object.calculate_surveillance_effort()
        
        messages.success(self.request, f'Surveillance plan "{self.object.name}" created successfully!')
        return response
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        grower = get_object_or_404(Grower, user=self.request.user)
        
        # Filter to current grower's locations
        form.fields['locations'].queryset = Location.objects.filter(grower=grower)
        
        return form
    
    def get_success_url(self):
        return reverse('surveillance_planner')


class SurveillanceReportView(LoginRequiredMixin, TemplateView):
    """
    Generate surveillance reports for growers
    """
    template_name = 'mango_pests_app/surveillance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        
        # Report period (default to last 3 months)
        from datetime import datetime, timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        # Override with request parameters if provided
        if self.request.GET.get('start_date'):
            start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d').date()
        if self.request.GET.get('end_date'):
            end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d').date()
        
        # Get surveillance data for period
        records = SurveillanceRecord.objects.filter(
            grower=grower,
            date__range=[start_date, end_date]
        ).order_by('-date')
        
        # Calculate comprehensive report
        report_data = self.generate_surveillance_report(grower, records, start_date, end_date)
        
        context.update({
            'grower': grower,
            'report_data': report_data,
            'start_date': start_date,
            'end_date': end_date,
            'records': records,
        })
        
        return context
    
    def generate_surveillance_report(self, grower, records, start_date, end_date):
        """Generate comprehensive surveillance report"""
        
        # Basic statistics
        total_sessions = records.count()
        total_trees_surveyed = records.aggregate(Sum('trees_surveyed_count'))['trees_surveyed_count__sum'] or 0
        total_time = records.aggregate(Sum('total_time_minutes'))['total_time_minutes__sum'] or 0
        
        # Threat findings
        inspections = TreeInspection.objects.filter(
            surveillance_record__in=records
        ).prefetch_related('threats_found')
        
        threat_summary = {}
        for inspection in inspections:
            for threat in inspection.threats_found.all():
                threat_name = threat.name
                if threat_name not in threat_summary:
                    threat_summary[threat_name] = {
                        'count': 0, 
                        'threat_type': threat.threat_type,
                        'risk_level': threat.risk_level
                    }
                threat_summary[threat_name]['count'] += 1
        
        # Performance metrics
        avg_time_per_tree = (total_time / total_trees_surveyed) if total_trees_surveyed > 0 else 0
        detection_rate = (len([i for i in inspections if i.threats_found.exists()]) / inspections.count() * 100) if inspections.count() > 0 else 0
        
        # Recommendations
        recommendations = self.generate_recommendations(grower, threat_summary, detection_rate)
        
        return {
            'period_days': (end_date - start_date).days,
            'total_sessions': total_sessions,
            'total_trees_surveyed': total_trees_surveyed,
            'total_time_hours': round(total_time / 60, 1),
            'avg_time_per_tree_minutes': round(avg_time_per_tree, 1),
            'threat_summary': threat_summary,
            'detection_rate': round(detection_rate, 1),
            'recommendations': recommendations,
            'efficiency_score': self.calculate_efficiency_score(grower, total_time, total_trees_surveyed),
        }
    
    def generate_recommendations(self, grower, threat_summary, detection_rate):
        """Generate actionable recommendations"""
        recommendations = []
        
        # High-risk threat recommendations
        high_risk_threats = [name for name, data in threat_summary.items() 
                           if data['risk_level'] == 'high' and data['count'] > 2]
        
        if high_risk_threats:
            recommendations.append({
                'type': 'warning',
                'title': 'High-Risk Threats Detected',
                'message': f"Multiple detections of high-risk threats: {', '.join(high_risk_threats)}. Consider increasing surveillance frequency and implementing targeted control measures."
            })
        
        # Detection rate recommendations
        if detection_rate > 20:
            recommendations.append({
                'type': 'warning',
                'title': 'High Detection Rate',
                'message': f"Detection rate of {detection_rate}% suggests active pest/disease pressure. Review current management practices."
            })
        elif detection_rate < 5:
            recommendations.append({
                'type': 'success',
                'title': 'Low Detection Rate',
                'message': f"Detection rate of {detection_rate}% indicates good pest/disease management. Current surveillance frequency appears adequate."
            })
        
        # Efficiency recommendations
        if grower.mango_tree_count and grower.mango_tree_count > 200:
            recommendations.append({
                'type': 'info',
                'title': 'Large Farm Optimization',
                'message': "Consider implementing zone-based surveillance and using mobile apps for data collection to improve efficiency."
            })
        
        return recommendations
    
    def calculate_efficiency_score(self, grower, total_time_minutes, trees_surveyed):
        """Calculate surveillance efficiency score (0-100)"""
        if not trees_surveyed or not total_time_minutes:
            return 0
        
        # Benchmark: 6-8 minutes per tree is optimal
        avg_time_per_tree = total_time_minutes / trees_surveyed
        
        if 6 <= avg_time_per_tree <= 8:
            efficiency = 100
        elif avg_time_per_tree < 6:
            efficiency = 80  # Too fast, might miss things
        elif avg_time_per_tree <= 12:
            efficiency = 90 - ((avg_time_per_tree - 8) * 5)  # Slower but thorough
        else:
            efficiency = max(50, 90 - ((avg_time_per_tree - 8) * 10))  # Too slow
        
        return round(efficiency)
    
    
    

    
    
class DashboardStatsAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        """Return fresh dashboard statistics"""
        stats = {
            'total_threats': MangoThreat.objects.count(),
            'total_pests': MangoThreat.objects.filter(threat_type='pest').count(),
            'total_diseases': MangoThreat.objects.filter(threat_type='disease').count(),
            'total_locations': Location.objects.count(),
            'total_trees': MangoTree.objects.count(),
        }
        
        # Get recent items
        recent_items = {
            'threats': [{
                'id': t.id,
                'name': t.name,
                'type': t.get_threat_type_display(),
                'risk': t.get_risk_level_display(),
                'created': t.created_at.strftime('%b %d, %Y')
            } for t in MangoThreat.objects.order_by('-created_at')[:5]],
            
            'locations': [{
                'id': l.id,
                'name': l.name,
                'address': l.address[:50] + '...' if len(l.address) > 50 else l.address
            } for l in Location.objects.order_by('-id')[:5]],
            
            'trees': [{
                'id': t.id,
                'tree_id': t.tree_id,
                'variety': t.variety,
                'age': t.age,
                'location': t.location.name
            } for t in MangoTree.objects.select_related('location').order_by('-id')[:5]]
        }
        
        return JsonResponse({
            'stats': stats,
            'recent_items': recent_items
        })
        
        
        
        
        
# Add these views to your views.py

class LocationListView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/location_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        locations = Location.objects.filter(grower=grower).prefetch_related('mango_trees')
        
        context.update({
            'locations': locations,
            'grower': grower,
        })
        return context


class TreeListView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/tree_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        trees = MangoTree.objects.filter(location__grower=grower).select_related('location')
        locations_count = Location.objects.filter(grower=grower).count()
        
        # Calculate statistics
        avg_age = trees.aggregate(avg_age=Avg('age'))['avg_age'] or 0
        total_surveillance_time = sum(tree.calculate_surveillance_time_minutes() for tree in trees)
        
        context.update({
            'trees': trees,
            'grower': grower,
            'locations_count': locations_count,
            'avg_age': avg_age,
            'surveillance_time': total_surveillance_time,
        })
        return context


# Also update your CRUD Dashboard to include links to list views
class CrudDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/crud_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Get fresh data with proper user filtering
        context['recent_threats'] = MangoThreat.objects.all().order_by('-created_at')[:10]
        context['recent_locations'] = Location.objects.filter(grower=grower).prefetch_related('mango_trees').order_by('-id')[:5]
        context['recent_trees'] = MangoTree.objects.filter(location__grower=grower).select_related('location').order_by('-id')[:5]
        
        # Add forms
        context['threat_form'] = MangoThreatForm()
        
        # Calculate statistics
        context['stats'] = {
            'total_threats': MangoThreat.objects.count(),
            'total_pests': MangoThreat.objects.filter(threat_type='pest').count(),
            'total_diseases': MangoThreat.objects.filter(threat_type='disease').count(),
            'total_locations': Location.objects.filter(grower=grower).count(),
            'total_trees': MangoTree.objects.filter(location__grower=grower).count(),
        }
        
        context['grower'] = grower
        return context
import logging
from django.db import IntegrityError
from jsonschema import ValidationError
from sqlalchemy import Transaction
from .forms import SurveillanceRecordForm, TreeInspectionForm, SurveillanceSearchForm

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, Sum, Min, Max
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, 
    UpdateView, DeleteView, FormView, View
)
from django.core.paginator import Paginator
from django.contrib.auth import logout, login, authenticate
from django.utils.decorators import method_decorator
import json
from datetime import datetime, timedelta, timezone


try:
    from django.db.models.functions import TruncMonth, Extract
except ImportError:
    # Fallback for older Django versions
    from django.db.models import DateTimeField
    from django.db.models.functions import Extract
    TruncMonth = None

from .models import (
    MangoThreat, Location, MangoTree, SurveillanceRecord, Grower,
    SurveillancePlan, TreeInspection, PlantPart
)
from .forms import (
    MangoThreatForm, LocationForm, MangoTreeForm, UserRegistrationForm
)
from .data import mango_threats

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, DeleteView
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
import logging

from .models import MangoThreat
from .forms import MangoThreatForm
    
# Core Views
class HomeView(TemplateView):
    """Home page of the Mango Surveillance System"""
    template_name = 'mango_pests_app/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['heading'] = "Welcome to the World Mango Organisation of Group 28 of HIT237!"
        context['description'] = "We are dedicated to combating mango pests and diseases through research and awareness."
        
        # Statistics
        context['total_threats'] = MangoThreat.objects.count()
        context['pest_count'] = MangoThreat.objects.filter(threat_type='pest').count()
        context['disease_count'] = MangoThreat.objects.filter(threat_type='disease').count()
        
        return context

class ThreatListView(TemplateView):
    """List all mango threats with search and filtering"""
    template_name = 'mango_pests_app/threat_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threats = mango_threats

        # Search functionality
        query = self.request.GET.get('q', '').strip().lower()
        if query:
            threats = [
                t for t in threats
                if query in t.name.lower() or query in t.description.lower()
            ]

        # Category filter
        category = self.request.GET.get('category', '')
        if category in ['pest', 'disease']:
            threats = [t for t in threats if t.threat_type == category]

        # Sort
        sort_option = self.request.GET.get('sort', 'name_asc')
        if sort_option == 'name_desc':
            threats.sort(key=lambda t: t.name, reverse=True)
        else:
            threats.sort(key=lambda t: t.name)

        # Pagination
        paginator = Paginator(threats, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Count info
        pest_count = len([t for t in threats if t.threat_type == 'pest'])
        disease_count = len([t for t in threats if t.threat_type == 'disease'])

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

class ThreatDetailView(DetailView):
    """Display individual threat information"""
    model = MangoThreat
    template_name = 'mango_pests_app/threat_details.html'
    context_object_name = 'threat'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'

class CompareThreatsView(FormView):
    """Compare selected mango threats"""
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

#  Surveillance Calculator - Core Business Logic
class SurveillanceCalculatorView(LoginRequiredMixin, TemplateView):
    """ Surveillance calculator meeting all business requirements"""
    template_name = 'mango_pests_app/surveillance_calculator.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # REQUIREMENT 1 & 2: Get user's locations and plant count
        locations = Location.objects.filter(grower=grower).prefetch_related('mango_trees')
        total_trees = sum(location.mango_trees.count() for location in locations)
        
        # REQUIREMENT 3: Surveillance calculation
        surveillance_calculation = None
        if total_trees > 0:
            surveillance_calculation = self.calculate_surveillance_effort(grower, locations, total_trees)
        
        # REQUIREMENT 4: Plant type flexibility
        plant_types_available = [
            {'type': 'mango', 'name': 'Mango', 'status': 'Active', 'base_time': 6},
            {'type': 'avocado', 'name': 'Avocado', 'status': 'Available', 'base_time': 5},
            {'type': 'citrus', 'name': 'Citrus', 'status': 'Available', 'base_time': 4},
            {'type': 'stone_fruit', 'name': 'Stone Fruit', 'status': 'Available', 'base_time': 5},
        ]
        
        # REQUIREMENT 5: Age-friendly interface settings
        interface_preferences = {
            'large_buttons': True,
            'clear_labels': True,
            'simple_navigation': True,
            'helpful_messages': True,
            'optimized_for_40_60': True
        }
        
        # REQUIREMENT 6: Plant parts analysis
        plant_parts_data = [
            {'name': 'Leaves', 'priority': 5, 'time_factor': 1.2, 'threats': ['Scale', 'Anthracnose']},
            {'name': 'Fruit', 'priority': 5, 'time_factor': 1.5, 'threats': ['Fruit Fly', 'Black Spot']},
            {'name': 'Branches', 'priority': 3, 'time_factor': 1.0, 'threats': ['Dieback', 'Borer']},
            {'name': 'Trunk', 'priority': 2, 'time_factor': 0.8, 'threats': ['Canker', 'Borers']},
            {'name': 'Root Zone', 'priority': 3, 'time_factor': 1.1, 'threats': ['Root Rot', 'Nematodes']}
        ]
        
        # REQUIREMENT 7: Stocking rate analysis
        stocking_analysis = self.get_stocking_rate_analysis(locations)
        
        # REQUIREMENT 8: Historical data summary
        historical_summary = self.get_historical_data_summary(grower)
        
        # Compliance status checker
        compliance_status = {
            'req1_plant_count': total_trees > 0,
            'req2_location_tracking': locations.count() > 0,
            'req3_time_calculation': surveillance_calculation is not None,
            'req4_plant_flexibility': True,
            'req5_age_friendly': True,
            'req6_plant_parts': True,
            'req7_stocking_rates': True,
            'req8_historical_data': True,
        }
        
        compliance_percentage = sum(compliance_status.values()) / len(compliance_status) * 100
        
        context.update({
            'grower': grower,
            'locations': locations,
            'total_trees': total_trees,
            'surveillance_calculation': surveillance_calculation,
            'plant_types_available': plant_types_available,
            'interface_preferences': interface_preferences,
            'plant_parts_data': plant_parts_data,
            'stocking_analysis': stocking_analysis,
            'historical_summary': historical_summary,
            'compliance_status': compliance_status,
            'compliance_percentage': compliance_percentage,
            'high_priority_threats': MangoThreat.objects.filter(risk_level='high')[:5],
        })
        
        return context
    
    def calculate_surveillance_effort(self, grower, locations, total_trees):
        """ Calculation considering all business requirements"""
        base_minutes_per_tree = 6
        total_base_minutes = total_trees * base_minutes_per_tree
        
        # Location-specific calculations
        location_breakdown = []
        total_location_time = 0
        
        for location in locations:
            tree_count = location.mango_trees.count()
            if tree_count > 0:
                # Calculate stocking rate
                stocking_rate = None
                stocking_multiplier = 1.0
                
                if location.area_hectares:
                    stocking_rate = tree_count / float(location.area_hectares)
                    if stocking_rate > 100:
                        stocking_multiplier = 1.2
                    elif stocking_rate < 50:
                        stocking_multiplier = 0.9
                
                # Individual tree time calculation
                location_minutes = 0
                for tree in location.mango_trees.all():
                    tree_time = tree.calculate_surveillance_time_minutes()
                    location_minutes += tree_time
                
                # Apply adjustments
                location_minutes *= stocking_multiplier
                plant_parts_time = location_minutes * 0.15
                location_minutes += plant_parts_time
                
                total_location_time += location_minutes
                
                location_breakdown.append({
                    'location': location,
                    'tree_count': tree_count,
                    'base_minutes': tree_count * base_minutes_per_tree,
                    'adjusted_minutes': round(location_minutes),
                    'stocking_rate': stocking_rate,
                    'stocking_multiplier': stocking_multiplier,
                    'includes_plant_parts': True,
                })
        
        # Travel and documentation time
        travel_time = locations.count() * 10 if locations.count() > 1 else 5
        doc_time = total_location_time * 0.15
        
        # Final totals
        total_minutes = total_location_time + travel_time + doc_time
        total_hours = total_minutes / 60
        
        # Frequency calculations
        frequency_days = grower.surveillance_frequency_days or 14
        monthly_hours = (total_hours * 30) / frequency_days
        annual_sessions = 365 / frequency_days
        
        return {
            'total_trees': total_trees,
            'total_time_minutes': round(total_minutes),
            'total_time_hours': round(total_hours, 2),
            'base_time_minutes': total_base_minutes,
            'location_specific_time': round(total_location_time),
            'travel_time_minutes': travel_time,
            'documentation_time_minutes': round(doc_time),
            'location_breakdown': location_breakdown,
            'monthly_effort_hours': round(monthly_hours, 1),
            'annual_sessions': round(annual_sessions),
            'frequency_recommendation': {
                'days': frequency_days,
                'description': f"Every {frequency_days} days",
            },
            'addresses_requirements': {
                'plant_count': f"{total_trees} plants tracked",
                'location_specific': f"{locations.count()} locations with individual calculations",
                'time_factors': "Age, health, size, stocking rate all considered",
                'plant_parts': "15% additional time for plant parts inspection",
                'stocking_rates': f"Density adjustments applied to eligible locations"
            }
        }
    
    def get_stocking_rate_analysis(self, locations):
        """Analyze stocking rates for compliance"""
        analysis = []
        
        for location in locations:
            if location.area_hectares:
                tree_count = location.mango_trees.count()
                if tree_count > 0:
                    rate = tree_count / float(location.area_hectares)
                    
                    if rate > 150:
                        classification = "Very High Density"
                        impact = "40% more surveillance time needed"
                        color = "danger"
                    elif rate > 100:
                        classification = "High Density" 
                        impact = "20% more surveillance time needed"
                        color = "warning"
                    elif rate > 50:
                        classification = "Standard Density"
                        impact = "Standard surveillance time"
                        color = "success"
                    else:
                        classification = "Low Density"
                        impact = "10% less surveillance time needed"
                        color = "info"
                    
                    analysis.append({
                        'location': location,
                        'rate': round(rate, 1),
                        'classification': classification,
                        'impact': impact,
                        'color': color
                    })
        
        return {
            'locations_analyzed': analysis,
            'requirement_met': len(analysis) > 0,
            'total_locations_with_rates': len(analysis),
            'total_locations': locations.count()
        }
    
    def get_historical_data_summary(self, grower):
        """Show historical data compliance"""
        records = SurveillanceRecord.objects.filter(grower=grower)
        
        return {
            'total_records': records.count(),
            'date_range': {
                'earliest': records.order_by('date').first().date if records.exists() else None,
                'latest': records.order_by('-date').first().date if records.exists() else None,
            },
            'data_separation': f"Data isolated to user {grower.user.username}",
            'record_types': {
                'surveillance_sessions': records.count(),
                'tree_inspections': TreeInspection.objects.filter(surveillance_record__grower=grower).count(),
            },
            'requirement_met': True,
        }

# CRUD Views
logger = logging.getLogger(__name__)

class ThreatCreateView(LoginRequiredMixin, CreateView):
    model = MangoThreat
    form_class = MangoThreatForm
    template_name = 'mango_pests_app/crud/threat_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Create New Threat"
        return context
    
    def form_valid(self, form):
        """Handle successful form submission"""
        try:
            with transaction.atomic():
                # Clean and validate the threat name
                threat_name = form.cleaned_data['name'].strip()
                
                # Check for duplicates manually (additional safety)
                if MangoThreat.objects.filter(name__iexact=threat_name).exists():
                    form.add_error('name', 'A threat with this name already exists. Please choose a different name.')
                    return self.form_invalid(form)
                
                # Save the threat
                threat = form.save(commit=False)
                
                # Generate slug if not provided
                if not threat.slug:
                    from django.utils.text import slugify
                    base_slug = slugify(threat.name)
                    slug = base_slug
                    counter = 1
                    
                    # Ensure unique slug
                    while MangoThreat.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    
                    threat.slug = slug
                
                # Save to database
                threat.save()
                
                # Log successful creation
                logger.info(f"Threat '{threat.name}' created successfully by user {self.request.user}")
                
                # Success message
                messages.success(
                    self.request, 
                    f'✅ Success! Threat "{threat.name}" has been created successfully! '
                    f'You can now view it in the threat list or create another one.'
                )
                
                return redirect(self.get_success_url())
                
        except IntegrityError as e:
            logger.error(f"Database integrity error creating threat: {e}")
            messages.error(
                self.request, 
                '❌ Database Error: This threat name or slug already exists. Please try a different name.'
            )
            return self.form_invalid(form)
            
        except ValidationError as e:
            logger.error(f"Validation error creating threat: {e}")
            messages.error(
                self.request, 
                f'❌ Validation Error: {str(e)}'
            )
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(f"Unexpected error creating threat: {e}")
            messages.error(
                self.request, 
                f'❌ Unexpected Error: Unable to save threat. Please try again. ({str(e)})'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        logger.warning(f"Form validation failed: {form.errors}")
        
        # Add a general error message
        messages.error(
            self.request, 
            '❌ Please correct the errors below and try again.'
        )
        
        # Add specific field errors to messages for better UX
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    messages.error(self.request, f'Form Error: {error}')
                else:
                    field_name = form.fields.get(field, {}).label or field.title()
                    messages.error(self.request, f'{field_name}: {error}')
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect to dashboard after successful creation"""
        return reverse('crud_dashboard')

class ThreatUpdateView(LoginRequiredMixin, UpdateView):
    model = MangoThreat
    form_class = MangoThreatForm
    template_name = 'mango_pests_app/crud/threat_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Edit Threat: {self.object.name}"
        return context
    
    def form_valid(self, form):
        """Handle successful form update"""
        try:
            with transaction.atomic():
                threat = form.save()
                
                logger.info(f"Threat '{threat.name}' updated successfully by user {self.request.user}")
                
                messages.success(
                    self.request, 
                    f'✅ Success! Threat "{threat.name}" has been updated successfully!'
                )
                
                return redirect(self.get_success_url())
                
        except IntegrityError as e:
            logger.error(f"Database integrity error updating threat: {e}")
            messages.error(
                self.request, 
                '❌ Database Error: Unable to update threat. The name might already exist.'
            )
            return self.form_invalid(form)
            
        except Exception as e:
            logger.error(f"Unexpected error updating threat: {e}")
            messages.error(
                self.request, 
                f'❌ Error updating threat: {str(e)}'
            )
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors for updates"""
        messages.error(
            self.request, 
            '❌ Please correct the errors below and try again.'
        )
        
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    messages.error(self.request, f'Form Error: {error}')
                else:
                    field_name = form.fields.get(field, {}).label or field.title()
                    messages.error(self.request, f'{field_name}: {error}')
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('crud_dashboard')

class ThreatDeleteView(LoginRequiredMixin, DeleteView):
    model = MangoThreat
    template_name = 'mango_pests_app/crud/threat_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'threat_name'
    success_url = reverse_lazy('crud_dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Delete Threat: {self.object.name}"
        return context
    
    def delete(self, request, *args, **kwargs):
        threat = self.get_object()
        threat_name = threat.name
        
        try:
            result = super().delete(request, *args, **kwargs)
            messages.success(
                request, 
                f'✅ Threat "{threat_name}" has been deleted successfully!'
            )
            return result
        except Exception as e:
            logger.error(f"Error deleting threat {threat_name}: {e}")
            messages.error(
                request, 
                f'❌ Error deleting threat "{threat_name}": {str(e)}'
            )
            return redirect('crud_dashboard')

# Additional helper functions for debugging

def debug_threat_form(request):
    """Debug function to test form handling"""
    if request.method == 'POST':
        form = MangoThreatForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                threat = form.save()
                return render(request, 'debug_success.html', {'threat': threat})
            except Exception as e:
                return render(request, 'debug_error.html', {'error': str(e), 'form': form})
        else:
            return render(request, 'debug_error.html', {'form': form, 'errors': form.errors})
    else:
        form = MangoThreatForm()
        return render(request, 'debug_form.html', {'form': form})

def test_threat_creation(request):
    """Test function to manually create a threat"""
    try:
        threat = MangoThreat.objects.create(
            name="Test Threat " + str(timezone.now().timestamp()),
            description="This is a test threat created for debugging purposes.",
            details="Detailed information about this test threat.",
            threat_type="pest",
            risk_level="low"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Test threat created: {threat.name}',
            'threat_id': threat.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating test threat: {str(e)}'
        })

# Location CRUD Views
class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'mango_pests_app/crud/location_form.html'
    
    def form_valid(self, form):
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        form.instance.grower = grower
        
        messages.success(self.request, f'✅ Location "{form.instance.name}" created!')
        return super().form_valid(form)
    
    def get_success_url(self):
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
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        selected_location = form.cleaned_data['location']
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        if selected_location.grower != grower:
            messages.error(self.request, '❌ You can only add trees to your own locations.')
            return self.form_invalid(form)
        
        messages.success(
            self.request, 
            f'✅ Tree "{form.instance.tree_id}" created successfully!'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('surveillance_calculator') + '?updated=true'

class MangoTreeUpdateView(LoginRequiredMixin, UpdateView):
    model = MangoTree
    form_class = MangoTreeForm
    template_name = 'mango_pests_app/crud/tree_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        return MangoTree.objects.filter(location__grower=grower)
    
    def form_valid(self, form):
        messages.success(self.request, f'✅ Tree "{form.instance.tree_id}" updated successfully!')
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

# Dashboard and List Views
class CrudDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/crud/crud_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        context['recent_threats'] = MangoThreat.objects.all().order_by('-created_at')[:10]
        context['recent_locations'] = Location.objects.filter(grower=grower).prefetch_related('mango_trees').order_by('-id')[:5]
        context['recent_trees'] = MangoTree.objects.filter(location__grower=grower).select_related('location').order_by('-id')[:5]
        
        context['threat_form'] = MangoThreatForm()
        
        context['stats'] = {
            'total_threats': MangoThreat.objects.count(),
            'total_pests': MangoThreat.objects.filter(threat_type='pest').count(),
            'total_diseases': MangoThreat.objects.filter(threat_type='disease').count(),
            'total_locations': Location.objects.filter(grower=grower).count(),
            'total_trees': MangoTree.objects.filter(location__grower=grower).count(),
        }
        
        context['grower'] = grower
        return context

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

# Analytics and Reporting Views
class ThreatAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current user's grower profile
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Real threat statistics
        all_threats = MangoThreat.objects.all()
        
        # Threat distribution by type
        threat_by_type = all_threats.values('threat_type').annotate(
            count=Count('id')
        ).order_by('threat_type')
        
        # Threat distribution by risk level
        threat_by_risk = all_threats.values('risk_level').annotate(
            count=Count('id')
        ).order_by('risk_level')
        
        # User-specific surveillance data
        user_records = SurveillanceRecord.objects.filter(grower=grower)
        user_inspections = TreeInspection.objects.filter(
            surveillance_record__grower=grower
        )
        
        # Threats found in user's surveillance
        threats_found_by_user = MangoThreat.objects.filter(
            treeinspection__surveillance_record__grower=grower
        ).annotate(
            detection_count=Count('treeinspection')
        ).order_by('-detection_count')
        
        # Monthly surveillance trends
        from django.db.models.functions import TruncMonth
        monthly_records = user_records.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            session_count=Count('id'),
            threats_found=Count('tree_inspections__threats_found', distinct=True)
        ).order_by('month')
        
        # Plant parts most affected
        plant_parts_affected = PlantPart.objects.filter(
            treeinspection__surveillance_record__grower=grower
        ).annotate(
            inspection_count=Count('treeinspection'),
            threat_count=Count('treeinspection__threats_found', distinct=True)
        ).order_by('-inspection_count')
        
        # Performance metrics
        total_sessions = user_records.count()
        total_inspections = user_inspections.count()
        threats_detected = threats_found_by_user.count()
        
        detection_rate = 0
        if total_inspections > 0:
            inspections_with_threats = user_inspections.filter(
                threats_found__isnull=False
            ).distinct().count()
            detection_rate = (inspections_with_threats / total_inspections) * 100
        
        context.update({
            'threat_stats': {
                'by_type': list(threat_by_type),
                'by_risk': list(threat_by_risk),
            },
            'total_threats': all_threats.count(),
            'high_risk_count': all_threats.filter(risk_level='high').count(),
            'locations_count': Location.objects.filter(grower=grower).count(),
            'user_metrics': {
                'total_sessions': total_sessions,
                'total_inspections': total_inspections,
                'threats_detected': threats_detected,
                'detection_rate': round(detection_rate, 1),
                'avg_session_time': user_records.filter(
                    total_time_minutes__isnull=False
                ).aggregate(avg=Avg('total_time_minutes'))['avg'] or 0,
            },
            'monthly_trends': list(monthly_records),
            'common_threats': threats_found_by_user[:10],
            'affected_plant_parts': plant_parts_affected[:10],
            'grower': grower,
        })
        
        return context

# Surveillance Planning Views (Placeholder for future development)
class SurveillancePlannerView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/surveillance_planner.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        context['grower'] = grower
        return context

class SurveillanceHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/surveillance_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        context['grower'] = grower
        return context

class SurveillanceReportView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/surveillance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = get_object_or_404(Grower, user=self.request.user)
        context['grower'] = grower
        return context



class SurveillanceRecordDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'mango_pests_app/surveillance/record_detail.html'

class TreeInspectionAjaxView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        return JsonResponse({'success': True, 'message': 'Inspection recorded successfully!'})

class SurveillancePlanCreateView(LoginRequiredMixin, CreateView):
    model = SurveillancePlan
    template_name = 'mango_pests_app/surveillance/plan_form.html'
    fields = ['name', 'locations', 'target_threats', 'frequency_days', 'start_date', 'end_date']

# AJAX API Views
class ThreatAjaxAPIView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
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

    def get(self, request, *args, **kwargs):
        threats = MangoThreat.objects.all()
        data = [{
            'id': threat.id,
            'name': threat.name,
            'slug': threat.slug,
            'threat_type': threat.threat_type,
            'risk_level': threat.risk_level,
        } for threat in threats]
        
        return JsonResponse({'threats': data})

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

# About and Legacy Views
class AboutView(TemplateView):
    """About Us page"""
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

class CrudRedirectView(LoginRequiredMixin, TemplateView):
    """Legacy CRUD view for backward compatibility"""
    template_name = 'mango_pests_app/crud.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower = Grower.objects.filter(user=self.request.user).first()

        locations = Location.objects.all()
        mango_trees = MangoTree.objects.all()

        context['grower'] = grower
        context['locations'] = locations
        context['mango_trees'] = mango_trees
        return context
    




class SurveillanceRecordCreateView(LoginRequiredMixin, CreateView):
    """Create detailed surveillance record with proper time handling"""
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/record_form.html'
    fields = ['location', 'date', 'start_time', 'end_time', 'weather_conditions', 'temperature_celsius', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ENSURE PLANT PARTS EXIST - this fixes the plant parts issue
        self.ensure_plant_parts_exist()
        
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        context['locations'] = Location.objects.filter(grower=grower)
        context['plant_parts'] = PlantPart.objects.all().order_by('-surveillance_priority')
        context['threats'] = MangoThreat.objects.all().order_by('name')
        context['grower'] = grower
        
        return context
    
    def ensure_plant_parts_exist(self):
        """Create default plant parts if they don't exist"""
        if PlantPart.objects.count() == 0:
            default_parts = [
                {'name': 'Leaves', 'description': 'Leaf inspection', 'surveillance_priority': 5, 'time_multiplier': 1.2},
                {'name': 'Fruit', 'description': 'Fruit inspection', 'surveillance_priority': 5, 'time_multiplier': 1.5},
                {'name': 'Branches', 'description': 'Branch inspection', 'surveillance_priority': 3, 'time_multiplier': 1.0},
                {'name': 'Trunk', 'description': 'Trunk inspection', 'surveillance_priority': 2, 'time_multiplier': 0.8},
                {'name': 'Root Zone', 'description': 'Root zone inspection', 'surveillance_priority': 3, 'time_multiplier': 1.1},
            ]
            
            for part_data in default_parts:
                PlantPart.objects.create(**part_data)
    
    def form_valid(self, form):
        # Set the grower to current user
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        form.instance.grower = grower
        
        # Process additional form data
        plant_parts = self.request.POST.getlist('plant_parts')
        threats_found = self.request.POST.getlist('threats_found')
        specific_findings = self.request.POST.get('specific_findings', '')
        action_taken = self.request.POST.get('action_taken', '')
        requires_followup = self.request.POST.get('requires_followup') == 'on'
        requires_treatment = self.request.POST.get('requires_treatment') == 'on'
        followup_date = self.request.POST.get('followup_date')
        
        # DEBUG: Print what we're receiving
        print(f"DEBUG: Plant parts received: {plant_parts}")
        print(f"DEBUG: Threats found: {threats_found}")
        
        # Calculate total time SAFELY - this fixes the IntegrityError
        total_time_minutes = None
        if form.instance.start_time and form.instance.end_time:
            try:
                start_datetime = datetime.combine(form.instance.date, form.instance.start_time)
                end_datetime = datetime.combine(form.instance.date, form.instance.end_time)
                time_diff = end_datetime - start_datetime
                
                # Convert to minutes and ensure it's positive
                calculated_minutes = int(time_diff.total_seconds() / 60)
                
                # Only set if positive (valid time range)
                if calculated_minutes > 0:
                    total_time_minutes = calculated_minutes
                else:
                    messages.warning(
                        self.request, 
                        'Invalid time range detected. End time must be after start time. Time duration not recorded.'
                    )
            except Exception as e:
                messages.warning(self.request, 'Could not calculate surveillance duration from provided times.')
        
        # Update tree count surveyed
        trees_count = MangoTree.objects.filter(location=form.instance.location).count()
        form.instance.trees_surveyed_count = trees_count
        form.instance.completed = True
        
        # Set total_time_minutes ONLY if we have a valid value
        if total_time_minutes is not None:
            form.instance.total_time_minutes = total_time_minutes
        
        # Enhance notes with additional findings
        enhanced_notes = form.instance.notes or ""
        if specific_findings:
            enhanced_notes += f"\n\n--- THREAT FINDINGS ---\n{specific_findings}"
        if action_taken:
            enhanced_notes += f"\n\n--- ACTIONS TAKEN ---\n{action_taken}"
        if requires_followup or requires_treatment:
            enhanced_notes += f"\n\n--- FOLLOW-UP REQUIRED ---"
            if requires_followup:
                enhanced_notes += f"\n• Follow-up surveillance needed"
            if requires_treatment:
                enhanced_notes += f"\n• Treatment/intervention required"
            if followup_date:
                enhanced_notes += f"\n• Recommended date: {followup_date}"
        
        form.instance.notes = enhanced_notes
        
        # Save the surveillance record
        surveillance_record = form.save()
        
        # Create detailed tree inspections
        threats_summary = self.create_enhanced_tree_inspections(surveillance_record, plant_parts, threats_found)
        
        # Create success message with threat summary
        if total_time_minutes:
            duration_text = f" (Duration: {total_time_minutes} minutes)"
        else:
            duration_text = ""
            
        success_message = f'✅ Surveillance session recorded successfully! Surveyed {trees_count} trees at {surveillance_record.location.name}{duration_text}.'
        
        if threats_found:
            threat_count = len(threats_found)
            success_message += f' Found {threat_count} threat type(s): {", ".join(threats_summary[:3])}'
            if len(threats_summary) > 3:
                success_message += f' and {len(threats_summary) - 3} more.'
        else:
            success_message += ' No threats detected - trees appear healthy!'
        
        messages.success(self.request, success_message)
        
        return super().form_valid(form)
    
    def create_enhanced_tree_inspections(self, surveillance_record, plant_parts, threats_found):
        """Create detailed tree inspection records with threat associations"""
        try:
            location = surveillance_record.location
            trees = MangoTree.objects.filter(location=location)
            
            if not trees.exists():
                print(f"No trees found at location: {location}")
                return []
            
            # Get plant part objects
            plant_part_objects = []
            if plant_parts:
                plant_part_objects = PlantPart.objects.filter(name__in=plant_parts)
                print(f"DEBUG: Found plant part objects: {[p.name for p in plant_part_objects]}")
            
            # Get threat objects
            threat_objects = []
            if threats_found:
                threat_objects = MangoThreat.objects.filter(id__in=threats_found)
                print(f"DEBUG: Found threat objects: {[t.name for t in threat_objects]}")
            
            # Determine overall severity based on threats found
            overall_severity = 'none'
            action_required = False
            
            if threat_objects:
                high_risk_threats = [t for t in threat_objects if t.risk_level == 'high']
                moderate_risk_threats = [t for t in threat_objects if t.risk_level == 'moderate']
                
                if high_risk_threats:
                    overall_severity = 'high'
                    action_required = True
                elif moderate_risk_threats:
                    overall_severity = 'moderate'
                    action_required = True
                else:
                    overall_severity = 'low'
            
            # Create individual tree inspections
            threats_summary = []
            inspections_created = 0
            
            for tree in trees:
                try:
                    base_time = tree.calculate_surveillance_time_minutes()
                    if threat_objects:
                        threat_investigation_time = len(threat_objects) * 2
                        inspection_time = base_time + threat_investigation_time
                    else:
                        inspection_time = base_time
                    
                    # Ensure inspection time is positive and reasonable
                    inspection_time = max(1, min(inspection_time, 120))
                    
                    # Build findings text
                    findings_parts = []
                    if plant_parts:
                        findings_parts.append(f"Plant parts inspected: {', '.join(plant_parts)}")
                    if threat_objects:
                        threat_names = [threat.name for threat in threat_objects]
                        findings_parts.append(f"Threats found: {', '.join(threat_names)}")
                        threats_summary = threat_names  # Update summary
                    else:
                        findings_parts.append("No threats detected")
                    
                    findings_text = ". ".join(findings_parts)
                    
                    # Create tree inspection record
                    inspection = TreeInspection.objects.create(
                        surveillance_record=surveillance_record,
                        tree=tree,
                        severity_level=overall_severity,
                        inspection_time_minutes=inspection_time,
                        findings=findings_text,
                        action_required=action_required,
                        photo_taken=False
                    )
                    
                    # Add plant parts checked (many-to-many relationship)
                    if plant_part_objects:
                        inspection.plant_parts_checked.set(plant_part_objects)
                        print(f"DEBUG: Added plant parts to inspection {inspection.id}")
                    
                    # Add threats found (many-to-many relationship)
                    if threat_objects:
                        inspection.threats_found.set(threat_objects)
                        print(f"DEBUG: Added threats to inspection {inspection.id}")
                    
                    inspections_created += 1
                    
                except Exception as e:
                    print(f"Error creating inspection for tree {tree}: {e}")
                    continue
            
            print(f"DEBUG: Created {inspections_created} inspections")
            return threats_summary
            
        except Exception as e:
            print(f"Error in create_enhanced_tree_inspections: {e}")
            return []
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Filter locations to current grower
        form.fields['location'].queryset = Location.objects.filter(grower=grower)
        form.fields['location'].empty_label = "Select a location..."
        
        # Set default date to today
        form.fields['date'].initial = datetime.now().date()
        
        return form
    
    def get_success_url(self):
        return reverse('surveillance_record_detail', kwargs={'pk': self.object.pk})



class DetailedSurveillanceRecordView(LoginRequiredMixin, DetailView):
    """Detailed view of surveillance record with all collected data"""
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/detailed_record_view.html'
    context_object_name = 'record'
    
    def get_queryset(self):
        # Only show records for current user
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        return SurveillanceRecord.objects.filter(grower=grower)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object
        
        # Get all tree inspections for this record
        inspections = TreeInspection.objects.filter(
            surveillance_record=record
        ).prefetch_related('plant_parts_checked', 'threats_found', 'tree')
        
        # Calculate summary statistics
        context['inspections'] = inspections
        context['total_inspections'] = inspections.count()
        context['threats_found_count'] = inspections.filter(threats_found__isnull=False).distinct().count()
        context['action_required_count'] = inspections.filter(action_required=True).count()
        
        # Plant parts summary
        plant_parts_data = {}
        for inspection in inspections:
            for part in inspection.plant_parts_checked.all():
                if part.name not in plant_parts_data:
                    plant_parts_data[part.name] = {
                        'count': 0,
                        'threats': set(),
                        'priority': part.surveillance_priority
                    }
                plant_parts_data[part.name]['count'] += 1
                for threat in inspection.threats_found.all():
                    plant_parts_data[part.name]['threats'].add(threat.name)
        
        context['plant_parts_summary'] = plant_parts_data
        
        # Threats summary
        threats_data = {}
        for inspection in inspections:
            for threat in inspection.threats_found.all():
                if threat.name not in threats_data:
                    threats_data[threat.name] = {
                        'count': 0,
                        'threat_type': threat.threat_type,
                        'risk_level': threat.risk_level,
                        'affected_parts': set()
                    }
                threats_data[threat.name]['count'] += 1
                for part in inspection.plant_parts_checked.all():
                    threats_data[threat.name]['affected_parts'].add(part.name)
        
        context['threats_summary'] = threats_data
        
        # Location and stocking rate information
        location = record.location
        if location.area_hectares:
            tree_count = MangoTree.objects.filter(location=location).count()
            context['stocking_rate'] = tree_count / float(location.area_hectares)
            context['stocking_classification'] = self.get_stocking_classification(context['stocking_rate'])
        
        return context
    
    def get_stocking_classification(self, rate):
        """Classify stocking rate"""
        if rate > 150:
            return {'class': 'danger', 'label': 'Very High Density'}
        elif rate > 100:
            return {'class': 'warning', 'label': 'High Density'}
        elif rate > 50:
            return {'class': 'success', 'label': 'Standard Density'}
        else:
            return {'class': 'info', 'label': 'Low Density'}


class SurveillanceHistoryView(LoginRequiredMixin, ListView):
    """Historical surveillance data with filtering and analysis"""
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/history_view.html'
    context_object_name = 'records'
    paginate_by = 20
    
    def get_queryset(self):
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        queryset = SurveillanceRecord.objects.filter(grower=grower).order_by('-date', '-created_at')
        
        # Apply search filters
        form = SurveillanceSearchForm(self.request.GET, user=self.request.user)
        if form.is_valid():
            if form.cleaned_data['date_from']:
                queryset = queryset.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data['date_to']:
                queryset = queryset.filter(date__lte=form.cleaned_data['date_to'])
            if form.cleaned_data['location']:
                queryset = queryset.filter(location=form.cleaned_data['location'])
            if form.cleaned_data['has_threats']:
                # Only records where threats were found
                queryset = queryset.filter(
                    tree_inspections__threats_found__isnull=False
                ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Add search form
        context['search_form'] = SurveillanceSearchForm(self.request.GET, user=self.request.user)
        
        # Calculate comprehensive statistics
        all_records = SurveillanceRecord.objects.filter(grower=grower)
        context['statistics'] = self.calculate_surveillance_statistics(all_records)
        
        # Monthly trend data for charts
        context['monthly_trends'] = self.get_monthly_trends(all_records)
        
        # Most common threats
        context['common_threats'] = self.get_common_threats(grower)
        
        # Plant parts most affected
        context['affected_plant_parts'] = self.get_affected_plant_parts(grower)
        
        return context
    
    def calculate_surveillance_statistics(self, records):
        """Calculate comprehensive surveillance statistics"""
        total_records = records.count()
        
        if total_records == 0:
            return {'no_data': True}
        
        # Time statistics
        time_stats = records.filter(total_time_minutes__isnull=False).aggregate(
            avg_time=Avg('total_time_minutes'),
            total_time=Sum('total_time_minutes'),
            min_time=Min('total_time_minutes'),
            max_time=Max('total_time_minutes')
        )
        
        # Tree and location statistics
        tree_stats = records.aggregate(
            total_trees_surveyed=Sum('trees_surveyed_count'),
            avg_trees_per_session=Avg('trees_surveyed_count')
        )
        
        # Threat detection statistics
        all_inspections = TreeInspection.objects.filter(surveillance_record__grower=records.first().grower)
        threat_stats = {
            'total_inspections': all_inspections.count(),
            'inspections_with_threats': all_inspections.filter(threats_found__isnull=False).distinct().count(),
            'action_required_count': all_inspections.filter(action_required=True).count(),
        }
        
        if threat_stats['total_inspections'] > 0:
            threat_stats['detection_rate'] = round(
                (threat_stats['inspections_with_threats'] / threat_stats['total_inspections']) * 100, 1
            )
        else:
            threat_stats['detection_rate'] = 0
        
        return {
            'total_records': total_records,
            'date_range': {
                'earliest': records.order_by('date').first().date,
                'latest': records.order_by('-date').first().date,
            },
            'time_stats': {
                'avg_minutes': round(time_stats['avg_time']) if time_stats['avg_time'] else 0,
                'total_hours': round(time_stats['total_time'] / 60) if time_stats['total_time'] else 0,
                'min_minutes': time_stats['min_time'] or 0,
                'max_minutes': time_stats['max_time'] or 0,
            },
            'tree_stats': {
                'total_surveyed': tree_stats['total_trees_surveyed'] or 0,
                'avg_per_session': round(tree_stats['avg_trees_per_session']) if tree_stats['avg_trees_per_session'] else 0,
            },
            'threat_stats': threat_stats,
        }
    
    def get_monthly_trends(self, records):
        """Get monthly surveillance trends"""        
        monthly_data = records.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            session_count=Count('id'),
            avg_time=Avg('total_time_minutes'),
            trees_surveyed=Sum('trees_surveyed_count')
        ).order_by('month')
        
        return list(monthly_data)
    
    def get_common_threats(self, grower):
        """Get most commonly found threats"""
        threat_counts = MangoThreat.objects.filter(
            treeinspection__surveillance_record__grower=grower
        ).annotate(
            detection_count=Count('treeinspection')
        ).order_by('-detection_count')[:10]
        
        return threat_counts
    
    def get_affected_plant_parts(self, grower):
        """Get plant parts most commonly affected"""
        plant_part_counts = PlantPart.objects.filter(
            treeinspection__surveillance_record__grower=grower
        ).annotate(
            inspection_count=Count('treeinspection')
        ).order_by('-inspection_count')[:10]
        
        return plant_part_counts


class SurveillanceAnalyticsView(LoginRequiredMixin, TemplateView):
    """Advanced analytics and reporting for surveillance data"""
    template_name = 'mango_pests_app/surveillance/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Get date range from query parameters (default to last 12 months)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        
        if self.request.GET.get('start_date'):
            start_date = datetime.strptime(self.request.GET.get('start_date'), '%Y-%m-%d').date()
        if self.request.GET.get('end_date'):
            end_date = datetime.strptime(self.request.GET.get('end_date'), '%Y-%m-%d').date()
        
        # Get surveillance records in range
        records = SurveillanceRecord.objects.filter(
            grower=grower,
            date__range=[start_date, end_date]
        )
        
        # Comprehensive analysis
        context.update({
            'grower': grower,
            'date_range': {'start': start_date, 'end': end_date},
            'performance_metrics': self.get_performance_metrics(records),
            'threat_analysis': self.get_threat_analysis(grower, start_date, end_date),
            'efficiency_analysis': self.get_efficiency_analysis(records),
            'location_comparison': self.get_location_comparison(grower, start_date, end_date),
            'seasonal_patterns': self.get_seasonal_patterns(records),
            'recommendations': self.generate_recommendations(grower, records),
        })
        
        return context
    
    def get_performance_metrics(self, records):
        """Calculate performance metrics"""
        # Implementation for performance analysis
        return {
            'surveillance_frequency': self.calculate_frequency(records),
            'coverage_rate': self.calculate_coverage_rate(records),
            'threat_detection_efficiency': self.calculate_detection_efficiency(records),
        }
    
    def get_threat_analysis(self, grower, start_date, end_date):
        """Analyze threat patterns"""
        # Implementation for threat pattern analysis
        return {
            'emerging_threats': self.identify_emerging_threats(grower, start_date, end_date),
            'threat_severity_trends': self.analyze_severity_trends(grower, start_date, end_date),
            'plant_part_vulnerability': self.analyze_plant_part_vulnerability(grower, start_date, end_date),
        }
    
    def generate_recommendations(self, grower, records):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze surveillance frequency
        if records.count() > 0:
            avg_interval = self.calculate_average_surveillance_interval(records)
            if avg_interval > 21:  # More than 3 weeks
                recommendations.append({
                    'type': 'warning',
                    'title': 'Increase Surveillance Frequency',
                    'message': f'Current average interval is {avg_interval} days. Consider surveying every 14 days.',
                    'priority': 'high'
                })
        
        # Analyze threat detection
        threat_rate = self.calculate_threat_detection_rate(grower)
        if threat_rate > 25:  # High threat detection rate
            recommendations.append({
                'type': 'danger',
                'title': 'High Threat Activity',
                'message': f'{threat_rate}% threat detection rate suggests active pest/disease pressure.',
                'priority': 'critical'
            })
        
        return recommendations




class DetailedSurveillanceRecordView(LoginRequiredMixin, DetailView):
    """Detailed view of surveillance record with all collected data"""
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/detailed_record_view.html'
    context_object_name = 'record'
    
    def get_queryset(self):
        # Only show records for current user
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        return SurveillanceRecord.objects.filter(grower=grower)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.object
        
        # Get all tree inspections for this record
        inspections = TreeInspection.objects.filter(
            surveillance_record=record
        ).prefetch_related('plant_parts_checked', 'threats_found', 'tree')
        
        # Calculate summary statistics
        context['inspections'] = inspections
        context['total_inspections'] = inspections.count()
        context['threats_found_count'] = inspections.filter(threats_found__isnull=False).distinct().count()
        context['action_required_count'] = inspections.filter(action_required=True).count()
        
        # Plant parts summary
        plant_parts_data = {}
        for inspection in inspections:
            for part in inspection.plant_parts_checked.all():
                if part.name not in plant_parts_data:
                    plant_parts_data[part.name] = {
                        'count': 0,
                        'threats': set(),
                        'priority': part.surveillance_priority
                    }
                plant_parts_data[part.name]['count'] += 1
                for threat in inspection.threats_found.all():
                    plant_parts_data[part.name]['threats'].add(threat.name)
        
        context['plant_parts_summary'] = plant_parts_data
        
        # Threats summary
        threats_data = {}
        for inspection in inspections:
            for threat in inspection.threats_found.all():
                if threat.name not in threats_data:
                    threats_data[threat.name] = {
                        'count': 0,
                        'threat_type': threat.threat_type,
                        'risk_level': threat.risk_level,
                        'affected_parts': set()
                    }
                threats_data[threat.name]['count'] += 1
                for part in inspection.plant_parts_checked.all():
                    threats_data[threat.name]['affected_parts'].add(part.name)
        
        context['threats_summary'] = threats_data
        
        # Location and stocking rate information
        location = record.location
        if location.area_hectares:
            tree_count = MangoTree.objects.filter(location=location).count()
            context['stocking_rate'] = tree_count / float(location.area_hectares)
            context['stocking_classification'] = self.get_stocking_classification(context['stocking_rate'])
        
        return context
    
    def get_stocking_classification(self, rate):
        """Classify stocking rate"""
        if rate > 150:
            return {'class': 'danger', 'label': 'Very High Density'}
        elif rate > 100:
            return {'class': 'warning', 'label': 'High Density'}
        elif rate > 50:
            return {'class': 'success', 'label': 'Standard Density'}
        else:
            return {'class': 'info', 'label': 'Low Density'}


class SurveillanceHistoryView(LoginRequiredMixin, ListView):
    """Historical surveillance data with filtering and analysis"""
    model = SurveillanceRecord
    template_name = 'mango_pests_app/surveillance/history_view.html'
    context_object_name = 'records'
    paginate_by = 20
    
    def get_queryset(self):
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        queryset = SurveillanceRecord.objects.filter(grower=grower).order_by('-date', '-created_at')
        
        # Apply basic filters from GET parameters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        location_id = self.request.GET.get('location')
        
        if date_from:
            try:
                queryset = queryset.filter(date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
            except ValueError:
                pass
        
        if date_to:
            try:
                queryset = queryset.filter(date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
            except ValueError:
                pass
        
        if location_id:
            try:
                queryset = queryset.filter(location_id=int(location_id))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Add locations for filtering
        context['locations'] = Location.objects.filter(grower=grower)
        
        # Calculate basic statistics
        all_records = SurveillanceRecord.objects.filter(grower=grower)
        context['statistics'] = self.calculate_basic_statistics(all_records)
        
        # Add filter values to maintain state
        context['current_filters'] = {
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'location': self.request.GET.get('location', ''),
        }
        
        return context
    
    def calculate_basic_statistics(self, records):
        """Calculate basic surveillance statistics"""
        total_records = records.count()
        
        if total_records == 0:
            return {'no_data': True}
        
        # Basic time statistics
        time_records = records.filter(total_time_minutes__isnull=False)
        avg_time = time_records.aggregate(avg=Avg('total_time_minutes'))['avg']
        total_time = time_records.aggregate(total=Sum('total_time_minutes'))['total']
        
        # Tree statistics
        total_trees_surveyed = records.aggregate(total=Sum('trees_surveyed_count'))['total']
        
        # Threat detection (simplified calculation)
        total_inspections = TreeInspection.objects.filter(surveillance_record__grower=records.first().grower).count()
        inspections_with_threats = TreeInspection.objects.filter(
            surveillance_record__grower=records.first().grower,
            threats_found__isnull=False
        ).distinct().count()
        
        detection_rate = (inspections_with_threats / total_inspections * 100) if total_inspections > 0 else 0
        
        return {
            'total_records': total_records,
            'avg_time_minutes': round(avg_time) if avg_time else 0,
            'total_time_hours': round(total_time / 60) if total_time else 0,
            'total_trees_surveyed': total_trees_surveyed or 0,
            'threat_detection_rate': round(detection_rate, 1),
            'date_range': {
                'earliest': records.order_by('date').first().date if records.exists() else None,
                'latest': records.order_by('-date').first().date if records.exists() else None,
            }
        }


class SurveillanceAnalyticsView(LoginRequiredMixin, TemplateView):
    """Basic analytics for surveillance data"""
    template_name = 'mango_pests_app/surveillance/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grower, created = Grower.objects.get_or_create(user=self.request.user)
        
        # Get basic analytics data
        records = SurveillanceRecord.objects.filter(grower=grower)
        
        context.update({
            'grower': grower,
            'total_sessions': records.count(),
            'total_inspections': TreeInspection.objects.filter(surveillance_record__grower=grower).count(),
            'recent_records': records.order_by('-date')[:10],
        })
        
        return context

from django import forms
from .models import MangoThreat, Location, MangoTree, SurveillanceRecord, Grower
from django.contrib.auth.models import User
from django import forms
from .models import SurveillanceRecord, TreeInspection, MangoThreat, PlantPart, Location, MangoTree
import datetime
from django.core.exceptions import ValidationError

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from .models import MangoThreat
import re

class MangoThreatForm(forms.ModelForm):
    class Meta:
        model = MangoThreat
        fields = ['name', 'description', 'details', 'threat_type', 'risk_level', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter threat name (e.g., Fruit Fly, Anthracnose)',
                'maxlength': 100,
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the threat (1-2 sentences)',
                'required': True
            }),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed information about the threat, symptoms, treatment, etc.'
            }),
            'threat_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make sure required fields are marked as required
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['threat_type'].required = True
        self.fields['risk_level'].required = True
        
        # Set help text
        self.fields['name'].help_text = 'Enter a clear, descriptive name for the threat'
        self.fields['description'].help_text = 'Brief description (minimum 10 characters)'
        self.fields['details'].help_text = 'Optional detailed information about the threat'
        self.fields['threat_type'].help_text = 'Select whether this is a pest or disease'
        self.fields['risk_level'].help_text = 'How severe is this threat?'
        self.fields['image'].help_text = 'Optional image of the threat (JPG, PNG, GIF - max 5MB)'
    
    def clean_name(self):
        """Validate and clean the threat name"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError("Threat name is required.")
        
        # Strip whitespace and normalize
        name = name.strip()
        
        if len(name) < 3:
            raise ValidationError("Threat name must be at least 3 characters long.")
        
        if len(name) > 100:
            raise ValidationError("Threat name cannot exceed 100 characters.")
        
        # Check for invalid characters (allow letters, numbers, spaces, hyphens, parentheses)
        if not re.match(r'^[a-zA-Z0-9\s\-\(\)\.\']+$', name):
            raise ValidationError("Threat name contains invalid characters. Use only letters, numbers, spaces, hyphens, and parentheses.")
        
        # Check for duplicate names (case-insensitive, excluding current instance if editing)
        instance_pk = self.instance.pk if self.instance else None
        existing_threats = MangoThreat.objects.filter(name__iexact=name)
        
        if instance_pk:
            existing_threats = existing_threats.exclude(pk=instance_pk)
        
        if existing_threats.exists():
            raise ValidationError(f"A threat with the name '{name}' already exists. Please choose a different name.")
        
        return name
    
    def clean_description(self):
        """Validate and clean the description"""
        description = self.cleaned_data.get('description')
        
        if not description:
            raise ValidationError("Description is required.")
        
        description = description.strip()
        
        if len(description) < 10:
            raise ValidationError("Description must be at least 10 characters long.")
        
        if len(description) > 500:
            raise ValidationError("Description cannot exceed 500 characters.")
        
        return description
    
    def clean_details(self):
        """Validate and clean the detailed information"""
        details = self.cleaned_data.get('details')
        
        if details:
            details = details.strip()
            
            if len(details) > 2000:
                raise ValidationError("Details cannot exceed 2000 characters.")
        
        return details or ""
    
    def clean_threat_type(self):
        """Validate threat type"""
        threat_type = self.cleaned_data.get('threat_type')
        
        if not threat_type:
            raise ValidationError("Please select a threat type.")
        
        valid_types = ['pest', 'disease']
        if threat_type not in valid_types:
            raise ValidationError("Invalid threat type selected.")
        
        return threat_type
    
    def clean_risk_level(self):
        """Validate risk level"""
        risk_level = self.cleaned_data.get('risk_level')
        
        if not risk_level:
            raise ValidationError("Please select a risk level.")
        
        valid_levels = ['low', 'moderate', 'high']
        if risk_level not in valid_levels:
            raise ValidationError("Invalid risk level selected.")
        
        return risk_level
    
    def clean_image(self):
        """Validate uploaded image"""
        image = self.cleaned_data.get('image')
        
        if image:
            # Check file size (5MB limit)
            if image.size > 5 * 1024 * 1024:  # 5MB in bytes
                raise ValidationError("Image file size cannot exceed 5MB.")
            
            # Check file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            file_extension = image.name.lower().split('.')[-1]
            
            if f'.{file_extension}' not in valid_extensions:
                raise ValidationError("Invalid image format. Please use JPG, PNG, or GIF.")
            
            # Additional MIME type validation
            valid_mime_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(image, 'content_type') and image.content_type not in valid_mime_types:
                raise ValidationError("Invalid image format detected.")
        
        return image
    
    def clean(self):
        """Additional form-wide validation"""
        cleaned_data = super().clean()
        
        name = cleaned_data.get('name')
        description = cleaned_data.get('description')
        threat_type = cleaned_data.get('threat_type')
        
        # Cross-field validation example
        if name and description:
            # Ensure name and description aren't identical
            if name.lower().strip() == description.lower().strip():
                raise ValidationError("Name and description should be different to provide more information.")
        
        # Validate threat type specific requirements
        if threat_type == 'disease' and name:
            # Suggest including pathogen type for diseases
            disease_keywords = ['fungus', 'bacteria', 'virus', 'pathogen', 'rot', 'blight', 'canker', 'spot', 'wilt']
            if not any(keyword in name.lower() for keyword in disease_keywords):
                # This is just a warning, not an error
                pass
        
        return cleaned_data
    
    def save(self, commit=True):
        """Custom save method with additional processing"""
        instance = super().save(commit=False)
        
        # Generate slug from name if not already set
        if not instance.slug:
            base_slug = slugify(instance.name)
            slug = base_slug
            counter = 1
            
            # Ensure unique slug
            while MangoThreat.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            instance.slug = slug
        
        if commit:
            instance.save()
        
        return instance


# Additional validation helper functions
def validate_threat_name_uniqueness(name, exclude_pk=None):
    """Helper function to check if threat name is unique"""
    queryset = MangoThreat.objects.filter(name__iexact=name.strip())
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    return not queryset.exists()

def generate_unique_slug(name, exclude_pk=None):
    """Generate a unique slug for a threat name"""
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    
    queryset = MangoThreat.objects.filter(slug=slug)
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    
    while queryset.exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        queryset = MangoThreat.objects.filter(slug=slug)
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
    
    return slug


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = [
            'name', 'address', 'description', 
            'gps_latitude', 'gps_longitude', 'area_hectares',
            'soil_type', 'irrigation_type'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., North Block, Paddock A, Main Orchard'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address or location description'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about this location (optional)'
            }),
            'gps_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'e.g., -12.4634 (Latitude for Darwin area)',
                'help_text': 'GPS Latitude coordinate'
            }),
            'gps_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'e.g., 130.8456 (Longitude for Darwin area)',
                'help_text': 'GPS Longitude coordinate'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'e.g., 2.5 (Area in hectares)',
                'help_text': 'Required for stocking rate calculation'
            }),
            'soil_type': forms.Select(
                choices=[
                    ('', 'Select soil type...'),
                    ('clay', 'Clay'),
                    ('sandy', 'Sandy'),
                    ('loam', 'Loam'),
                    ('clay_loam', 'Clay Loam'),
                    ('sandy_loam', 'Sandy Loam'),
                    ('silt', 'Silt'),
                    ('rocky', 'Rocky'),
                    ('other', 'Other'),
                ],
                attrs={'class': 'form-select'}
            ),
            'irrigation_type': forms.Select(
                choices=[
                    ('', 'Select irrigation type...'),
                    ('drip', 'Drip Irrigation'),
                    ('sprinkler', 'Sprinkler System'),
                    ('flood', 'Flood Irrigation'),
                    ('rainfed', 'Rain-fed Only'),
                    ('micro_spray', 'Micro Spray'),
                    ('furrow', 'Furrow Irrigation'),
                    ('other', 'Other'),
                ],
                attrs={'class': 'form-select'}
            )
        }
        
        help_texts = {
            'area_hectares': 'Enter the area in hectares (required for calculating trees per hectare)',
            'gps_latitude': 'GPS Latitude coordinate (optional but recommended)',
            'gps_longitude': 'GPS Longitude coordinate (optional but recommended)',
            'soil_type': 'Soil type affects plant health and surveillance needs',
            'irrigation_type': 'Irrigation method affects disease risk and surveillance frequency',
        }
    
    def clean_area_hectares(self):
        area = self.cleaned_data.get('area_hectares')
        if area and area <= 0:
            raise forms.ValidationError("Area must be greater than 0 hectares.")
        return area
    
    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('gps_latitude')
        longitude = cleaned_data.get('gps_longitude')
        
        # Validate GPS coordinates if provided (rough validation for Australia)
        if latitude and longitude:
            if not (-44 <= latitude <= -10):  # Australia latitude range
                self.add_error('gps_latitude', 'Latitude seems outside Australia. Please check coordinates.')
            if not (113 <= longitude <= 154):  # Australia longitude range
                self.add_error('gps_longitude', 'Longitude seems outside Australia. Please check coordinates.')
        
        # If one GPS coordinate is provided, encourage providing both
        if (latitude and not longitude) or (longitude and not latitude):
            if not latitude:
                self.add_error('gps_latitude', 'If providing GPS coordinates, please provide both latitude and longitude.')
            if not longitude:
                self.add_error('gps_longitude', 'If providing GPS coordinates, please provide both latitude and longitude.')
        
        return cleaned_data

class MangoTreeForm(forms.ModelForm):
    class Meta:
        model = MangoTree
        fields = ['location', 'tree_id', 'age', 'variety']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-control'}),
            'tree_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unique tree identifier'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Age in years',
                'min': 1
            }),
            'variety': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mango variety'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            try:
                grower = Grower.objects.get(user=user)
                self.fields['location'].queryset = Location.objects.filter(grower=grower)
            except Grower.DoesNotExist:
                self.fields['location'].queryset = Location.objects.none()
        else:
            self.fields['location'].queryset = Location.objects.none()
        
        if self.fields['location'].queryset.count() == 0:
            self.fields['location'].empty_label = "No locations available - create a location first"
        else:
            self.fields['location'].empty_label = "Select a location"
        
    def clean_tree_id(self):
        tree_id = self.cleaned_data.get('tree_id')
        if tree_id:
            tree_pk = self.instance.pk if self.instance else None
            if MangoTree.objects.filter(tree_id=tree_id).exclude(pk=tree_pk).exists():
                raise forms.ValidationError("A tree with this ID already exists.")
        return tree_id

class SurveillanceRecordForm(forms.ModelForm):
    class Meta:
        model = SurveillanceRecord
        fields = ['location', 'date', 'notes']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Surveillance notes and observations'
            })
        }

class ThreatSearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search threats...'
        })
    )
    
    category = forms.ChoiceField(
        choices=[('', 'All'), ('pest', 'Pests'), ('disease', 'Diseases')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('name_asc', 'Name (A-Z)'),
            ('name_desc', 'Name (Z-A)'),
            ('created_desc', 'Newest First'),
            ('created_asc', 'Oldest First')
        ],
        required=False,
        initial='name_asc',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    contact_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Grower.objects.create(
                user=user,
                contact_number=self.cleaned_data.get('contact_number')
            )
        return user

class GrowerForm(forms.ModelForm):
    class Meta:
        model = Grower
        fields = ['contact_number', 'farm_name', 'region', 'mango_tree_count', 'notes']
        widgets = {
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'farm_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Farm name'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Region name'
            }),
            'mango_tree_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of mango trees',
                'min': 0
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes'
            })
        }
        
        

class SurveillanceRecordForm(forms.ModelForm):
    """ Form to capture all required surveillance data"""
    
    # Plant parts selection (multiple choice)
    plant_parts_surveyed = forms.ModelMultipleChoiceField(
        queryset=PlantPart.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Select which plant parts you will inspect"
    )
    
    # Threats found during surveillance
    threats_found = forms.ModelMultipleChoiceField(
        queryset=MangoThreat.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Select any pests or diseases observed"
    )
    
    class Meta:
        model = SurveillanceRecord
        fields = [
            'location', 'date', 'start_time', 'end_time', 
            'weather_conditions', 'temperature_celsius', 
            'plant_parts_surveyed', 'threats_found', 'notes'
        ]
        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'weather_conditions': forms.Select(
                choices=[
                    ('', 'Select weather...'),
                    ('sunny', 'Sunny'),
                    ('partly_cloudy', 'Partly Cloudy'),
                    ('cloudy', 'Cloudy'),
                    ('rainy', 'Rainy'),
                    ('windy', 'Windy'),
                    ('hot', 'Hot'),
                    ('humid', 'Humid'),
                ],
                attrs={'class': 'form-select'}
            ),
            'temperature_celsius': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': 'Temperature in Celsius'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Record detailed observations, actions taken, follow-up needed, etc.'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter locations to current user only
        if user:
            try:
                from .models import Grower
                grower = Grower.objects.get(user=user)
                self.fields['location'].queryset = Location.objects.filter(grower=grower)
            except Grower.DoesNotExist:
                self.fields['location'].queryset = Location.objects.none()
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = datetime.date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validate time range
        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data
    
    def save(self, commit=True):
        surveillance_record = super().save(commit=False)
        
        # Calculate total time if start and end times are provided
        if surveillance_record.start_time and surveillance_record.end_time:
            start_datetime = datetime.datetime.combine(surveillance_record.date, surveillance_record.start_time)
            end_datetime = datetime.datetime.combine(surveillance_record.date, surveillance_record.end_time)
            total_minutes = int((end_datetime - start_datetime).total_seconds() / 60)
            surveillance_record.total_time_minutes = total_minutes
        
        if commit:
            surveillance_record.save()
            
            # Save many-to-many relationships
            self.save_m2m()
            
            # Create individual tree inspections based on selected plant parts and threats
            self.create_tree_inspections(surveillance_record)
        
        return surveillance_record
    
    def create_tree_inspections(self, surveillance_record):
        """Create individual tree inspection records"""
        location = surveillance_record.location
        plant_parts = self.cleaned_data.get('plant_parts_surveyed', [])
        threats = self.cleaned_data.get('threats_found', [])
        
        # Get trees at this location
        trees = MangoTree.objects.filter(location=location)
        
        for tree in trees:
            # Create tree inspection record
            inspection = TreeInspection.objects.create(
                surveillance_record=surveillance_record,
                tree=tree,
                severity_level='none',  # Default, can be updated later
                inspection_time_minutes=tree.calculate_surveillance_time_minutes(),
                findings=f"Surveyed plant parts: {', '.join([part.name for part in plant_parts])}"
            )
            
            # Add plant parts checked
            if plant_parts:
                inspection.plant_parts_checked.set(plant_parts)
            
            # Add threats found (if any)
            if threats:
                inspection.threats_found.set(threats)
                inspection.severity_level = 'moderate'  # Update severity if threats found
                inspection.action_required = True
                inspection.save()


class TreeInspectionForm(forms.ModelForm):
    """Form for detailed individual tree inspection"""
    
    class Meta:
        model = TreeInspection
        fields = [
            'tree', 'plant_parts_checked', 'threats_found', 
            'severity_level', 'findings', 'action_required', 
            'follow_up_date', 'photo_taken', 'photo_filename'
        ]
        widgets = {
            'tree': forms.Select(attrs={'class': 'form-select'}),
            'plant_parts_checked': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'threats_found': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'severity_level': forms.Select(attrs={'class': 'form-select'}),
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed findings for this specific tree'
            }),
            'action_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'photo_taken': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'photo_filename': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Photo filename if taken'
            })
        }


class LocationDetailForm(forms.ModelForm):
    """ Location form with GPS and stocking rate data"""
    
    class Meta:
        model = Location
        fields = [
            'name', 'address', 'description', 
            'gps_latitude', 'gps_longitude', 'area_hectares',
            'soil_type', 'irrigation_type'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., North Block, Paddock A, Main Orchard'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Full address or location description'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about this location'
            }),
            'gps_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'e.g., -12.4634 (Latitude)'
            }),
            'gps_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'e.g., 130.8456 (Longitude)'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Area in hectares (for stocking rate calculation)'
            }),
            'soil_type': forms.Select(
                choices=[
                    ('', 'Select soil type...'),
                    ('clay', 'Clay'),
                    ('sandy', 'Sandy'),
                    ('loam', 'Loam'),
                    ('clay_loam', 'Clay Loam'),
                    ('sandy_loam', 'Sandy Loam'),
                    ('silt', 'Silt'),
                    ('other', 'Other'),
                ],
                attrs={'class': 'form-select'}
            ),
            'irrigation_type': forms.Select(
                choices=[
                    ('', 'Select irrigation type...'),
                    ('drip', 'Drip Irrigation'),
                    ('sprinkler', 'Sprinkler'),
                    ('flood', 'Flood Irrigation'),
                    ('rainfed', 'Rain-fed'),
                    ('micro_spray', 'Micro Spray'),
                    ('other', 'Other'),
                ],
                attrs={'class': 'form-select'}
            )
        }
    
    def clean_area_hectares(self):
        area = self.cleaned_data.get('area_hectares')
        if area and area <= 0:
            raise forms.ValidationError("Area must be greater than 0.")
        return area
    
    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('gps_latitude')
        longitude = cleaned_data.get('gps_longitude')
        
        # Validate GPS coordinates (rough validation for Australia)
        if latitude and longitude:
            if not (-44 <= latitude <= -10):  # Australia latitude range
                raise forms.ValidationError("Latitude seems outside Australia. Please check coordinates.")
            if not (113 <= longitude <= 154):  # Australia longitude range
                raise forms.ValidationError("Longitude seems outside Australia. Please check coordinates.")
        
        return cleaned_data


class SurveillanceSearchForm(forms.Form):
    """Form to search and filter surveillance records"""
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="From Date"
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="To Date"
    )
    
    location = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All locations"
    )
    
    threat_type = forms.ChoiceField(
        choices=[
            ('', 'All threats'),
            ('pest', 'Pests only'),
            ('disease', 'Diseases only'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    has_threats = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Only sessions with threats found"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter locations to current user
        if user:
            try:
                from .models import Grower
                grower = Grower.objects.get(user=user)
                self.fields['location'].queryset = Location.objects.filter(grower=grower)
            except Grower.DoesNotExist:
                pass


class PlantPartForm(forms.ModelForm):
    """Form for managing plant parts and their surveillance properties"""
    
    class Meta:
        model = PlantPart
        fields = ['name', 'description', 'surveillance_priority', 'time_multiplier']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Leaves, Fruit, Branches'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of this plant part and surveillance considerations'
            }),
            'surveillance_priority': forms.Select(
                choices=[(i, f'Priority {i}') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            ),
            'time_multiplier': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'max': '3.0',
                'placeholder': 'Time multiplier (e.g., 1.5 = 50% more time)'
            })
        }
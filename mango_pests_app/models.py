# models.py - ENHANCED FOR SURVEILLANCE CALCULATOR

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import datetime

class Grower(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    farm_name = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    mango_tree_count = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # New fields for surveillance calculations
    farm_size_hectares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stocking_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                      help_text="Trees per hectare")
    surveillance_frequency_days = models.PositiveIntegerField(default=14, 
                                                            help_text="Default surveillance interval in days")

    def __str__(self):
        return f"{self.user.username} - {self.farm_name or 'Unknown Farm'}"

    def calculate_recommended_surveillance_effort(self):
        """Calculate recommended surveillance effort based on farm parameters"""
        if not all([self.mango_tree_count, self.farm_size_hectares]):
            return None
        
        # Base calculation: trees * complexity factor * risk multiplier
        base_effort_hours = self.mango_tree_count * 0.1  # 6 minutes per tree
        
        # Adjust for farm density
        if self.stocking_rate:
            if self.stocking_rate > 100:  # High density
                base_effort_hours *= 1.2
            elif self.stocking_rate < 50:  # Low density
                base_effort_hours *= 0.9
        
        return round(base_effort_hours, 2)


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField(null=True, blank=True)
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, related_name="locations", null=True, blank=True)
    
    # Enhanced location data for surveillance
    gps_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    gps_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    area_hectares = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    soil_type = models.CharField(max_length=50, null=True, blank=True)
    irrigation_type = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.address}"


class PlantPart(models.Model):
    """Different parts of plants that can be surveilled"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    surveillance_priority = models.IntegerField(default=1, 
                                              validators=[MinValueValidator(1), MaxValueValidator(5)],
                                              help_text="Priority 1=Low, 5=Critical")
    
    def __str__(self):
        return self.name


class MangoTree(models.Model):
    VARIETY_CHOICES = [
        ('kensington_pride', 'Kensington Pride'),
        ('calypso', 'Calypso'),
        ('honey_gold', 'Honey Gold'),
        ('r2e2', 'R2E2'),
        ('keitt', 'Keitt'),
        ('kent', 'Kent'),
        ('other', 'Other'),
    ]
    
    AGE_GROUP_CHOICES = [
        ('young', '0-3 years'),
        ('juvenile', '4-7 years'), 
        ('mature', '8-15 years'),
        ('old', '16+ years'),
    ]
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="mango_trees")
    tree_id = models.CharField(max_length=100, unique=True)
    age = models.PositiveIntegerField()
    variety = models.CharField(max_length=50, choices=VARIETY_CHOICES, default='kensington_pride')
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, null=True, blank=True)
    
    # Enhanced surveillance data
    height_meters = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    canopy_diameter_meters = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    health_status = models.CharField(max_length=20, 
                                   choices=[('excellent', 'Excellent'), ('good', 'Good'), 
                                           ('fair', 'Fair'), ('poor', 'Poor')], 
                                   default='good')
    
    def save(self, *args, **kwargs):
        # Automatically set age group based on age
        if self.age <= 3:
            self.age_group = 'young'
        elif self.age <= 7:
            self.age_group = 'juvenile'
        elif self.age <= 15:
            self.age_group = 'mature'
        else:
            self.age_group = 'old'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.variety} ({self.tree_id}) - Age: {self.age}"

    def calculate_surveillance_time_minutes(self):
        """Calculate recommended surveillance time per tree"""
        base_time = 5  # Base 5 minutes per tree
        
        # Adjust for age group
        age_multipliers = {
            'young': 0.7,
            'juvenile': 0.9,
            'mature': 1.0,
            'old': 1.2
        }
        
        # Adjust for tree size
        size_multiplier = 1.0
        if self.height_meters and self.height_meters > 4:
            size_multiplier = 1.3
        elif self.height_meters and self.height_meters < 2:
            size_multiplier = 0.8
            
        # Adjust for health status
        health_multipliers = {
            'excellent': 0.8,
            'good': 1.0,
            'fair': 1.3,
            'poor': 1.5
        }
        
        total_time = (base_time * 
                     age_multipliers.get(self.age_group, 1.0) * 
                     size_multiplier * 
                     health_multipliers.get(self.health_status, 1.0))
        
        return round(total_time, 1)



class MangoThreat(models.Model):
    THREAT_TYPES = [
        ('pest', 'Pest'),
        ('disease', 'Disease'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField()
    details = models.TextField()
    
    # CHANGE: Use ImageField instead of CharField
    image = models.ImageField(upload_to='threat_images/', null=True, blank=True, 
                             help_text="Upload an image of this threat")
    
    threat_type = models.CharField(max_length=10, choices=THREAT_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='moderate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('threat_details', kwargs={'threat_name': self.slug})
    
    def __str__(self):
        return f"{self.name} ({self.get_threat_type_display()})"




class SurveillancePlan(models.Model):
    """Master surveillance plan for a grower's property"""
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, related_name="surveillance_plans")
    name = models.CharField(max_length=100)
    locations = models.ManyToManyField(Location)
    target_threats = models.ManyToManyField(MangoThreat, blank=True)
    
    frequency_days = models.PositiveIntegerField(default=14)
    start_date = models.DateField(default=datetime.date.today)
    end_date = models.DateField(null=True, blank=True)
    
    total_estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.grower.farm_name} - {self.name}"
    
    def calculate_surveillance_effort(self):
        """Calculate total surveillance effort for this plan"""
        total_minutes = 0
        tree_count = 0
        
        for location in self.locations.all():
            for tree in location.mango_trees.all():
                total_minutes += tree.calculate_surveillance_time_minutes()
                tree_count += 1
        
        # Add overhead time (travel, setup, documentation)
        overhead_percentage = 0.3  # 30% overhead
        total_minutes_with_overhead = total_minutes * (1 + overhead_percentage)
        
        total_hours = total_minutes_with_overhead / 60
        self.total_estimated_hours = round(total_hours, 2)
        self.save()
        
        return {
            'total_hours': self.total_estimated_hours,
            'tree_count': tree_count,
            'average_minutes_per_tree': round(total_minutes / tree_count if tree_count > 0 else 0, 1)
        }


class SurveillanceRecord(models.Model):
    """Individual surveillance session record"""
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, related_name="surveillance_records")
    surveillance_plan = models.ForeignKey(SurveillancePlan, on_delete=models.CASCADE, 
                                        related_name="records", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    weather_conditions = models.CharField(max_length=100, null=True, blank=True)
    temperature_celsius = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    trees_surveyed_count = models.PositiveIntegerField(default=0)
    total_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Surveillance by {self.grower} at {self.location} on {self.date}"
    
    def calculate_actual_time(self):
        """Calculate actual surveillance time if start/end times provided"""
        if self.start_time and self.end_time:
            start_datetime = datetime.datetime.combine(self.date, self.start_time)
            end_datetime = datetime.datetime.combine(self.date, self.end_time)
            delta = end_datetime - start_datetime
            self.total_time_minutes = int(delta.total_seconds() / 60)
            self.save()
            return self.total_time_minutes
        return None


class TreeInspection(models.Model):
    """Individual tree inspection within a surveillance record"""
    surveillance_record = models.ForeignKey(SurveillanceRecord, on_delete=models.CASCADE, 
                                          related_name="tree_inspections")
    tree = models.ForeignKey(MangoTree, on_delete=models.CASCADE, related_name="inspections")
    plant_parts_checked = models.ManyToManyField(PlantPart)
    
    threats_found = models.ManyToManyField(MangoThreat, blank=True)
    
    # Inspection results
    severity_level = models.CharField(max_length=20, 
                                    choices=[('none', 'No Issues'), ('low', 'Low'), 
                                            ('moderate', 'Moderate'), ('high', 'High')],
                                    default='none')
    
    inspection_time_minutes = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    findings = models.TextField(null=True, blank=True)
    action_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Photo evidence
    photo_taken = models.BooleanField(default=False)
    photo_filename = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"Inspection of {self.tree} on {self.surveillance_record.date}"


# Keep original models for backward compatibility
class Pest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    risk_level = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')])

    def __str__(self):
        return f"{self.name} - Risk: {self.risk_level}"


class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    risk_level = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')])

    def __str__(self):
        return f"{self.name} - Risk: {self.risk_level}"


class Inspection(models.Model):
    record = models.ForeignKey(SurveillanceRecord, on_delete=models.CASCADE, related_name="inspections")
    tree = models.ForeignKey(MangoTree, on_delete=models.CASCADE, related_name="old_inspections")
    threat = models.ForeignKey(MangoThreat, null=True, blank=True, on_delete=models.SET_NULL)
    pest = models.ForeignKey(Pest, null=True, blank=True, on_delete=models.SET_NULL)
    disease = models.ForeignKey(Disease, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50, choices=[('Found', 'Found'), ('Controlled', 'Controlled'), ('Escalated', 'Escalated')])
    severity = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')])
    findings = models.TextField(null=True, blank=True)

    def __str__(self):
        details = []
        if self.threat:
            details.append(f"Threat: {self.threat}")
        if self.pest:
            details.append(f"Pest: {self.pest}")
        if self.disease:
            details.append(f"Disease: {self.disease}")
        return f"Inspection of {self.tree} - {' | '.join(details)}"

    def risk_assessment(self):
        risk_map = {'Low': 1, 'Moderate': 2, 'High': 3}
        
        if self.threat:
            threat_risk = risk_map.get(self.threat.risk_level.title(), 0)
            return ['Low', 'Moderate', 'High'][min(threat_risk - 1, 2)] if threat_risk > 0 else 'Low'
        
        pest_risk = risk_map.get(self.pest.risk_level, 0) if self.pest else 0
        disease_risk = risk_map.get(self.disease.risk_level, 0) if self.disease else 0
        total_risk = pest_risk + disease_risk
        
        if total_risk <= 2:
            return "Low"
        elif total_risk == 3:
            return "Moderate"
        else:
            return "High"
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify

class Grower(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return self.user.username


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.address}"


class MangoTree(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="mango_trees")
    tree_id = models.CharField(max_length=100, unique=True)
    age = models.PositiveIntegerField()
    variety = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.variety} ({self.tree_id}) - Age: {self.age}"


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
    image = models.CharField(max_length=255, default='default-threat.png')  # Store image filename
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


# Keep original Pest and Disease models for backward compatibility if needed
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


class SurveillanceRecord(models.Model):
    grower = models.ForeignKey(Grower, on_delete=models.CASCADE, related_name="surveillance_records")
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    date = models.DateField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Surveillance by {self.grower} at {self.location} on {self.date}"


class Inspection(models.Model):
    record = models.ForeignKey(SurveillanceRecord, on_delete=models.CASCADE, related_name="inspections")
    tree = models.ForeignKey(MangoTree, on_delete=models.CASCADE, related_name="inspections")
    # Updated to use the new MangoThreat model
    threat = models.ForeignKey(MangoThreat, null=True, blank=True, on_delete=models.SET_NULL)
    # Keep old fields for backward compatibility
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
        
        # Check new threat model first
        if self.threat:
            threat_risk = risk_map.get(self.threat.risk_level.title(), 0)
            return ['Low', 'Moderate', 'High'][min(threat_risk - 1, 2)] if threat_risk > 0 else 'Low'
        
        # Fallback to old models
        pest_risk = risk_map.get(self.pest.risk_level, 0) if self.pest else 0
        disease_risk = risk_map.get(self.disease.risk_level, 0) if self.disease else 0
        total_risk = pest_risk + disease_risk
        
        if total_risk <= 2:
            return "Low"
        elif total_risk == 3:
            return "Moderate"
        else:
            return "High"
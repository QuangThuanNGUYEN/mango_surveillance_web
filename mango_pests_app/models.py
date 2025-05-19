from django.db import models
from django.contrib.auth.models import User

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
    pest = models.ForeignKey(Pest, null=True, blank=True, on_delete=models.SET_NULL)
    disease = models.ForeignKey(Disease, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=50, choices=[('Found', 'Found'), ('Controlled', 'Controlled'), ('Escalated', 'Escalated')])
    severity = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Moderate', 'Moderate'), ('High', 'High')])
    findings = models.TextField(null=True, blank=True)

    def __str__(self):
        details = []
        if self.pest:
            details.append(f"Pest: {self.pest}")
        if self.disease:
            details.append(f"Disease: {self.disease}")
        return f"Inspection of {self.tree} - {' | '.join(details)}"


    def risk_assessment(self):
        risk_map = {'Low': 1, 'Moderate': 2, 'High': 3}
        pest_risk = risk_map.get(self.pest.risk_level, 0) if self.pest else 0
        disease_risk = risk_map.get(self.disease.risk_level, 0) if self.disease else 0
        total_risk = pest_risk + disease_risk
        
        if total_risk <= 2:
            return "Low"
        elif total_risk == 3:
            return "Moderate"
        else:
            return "High"

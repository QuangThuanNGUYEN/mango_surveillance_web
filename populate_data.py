# populate_data.py
# Run with: python manage.py shell < populate_data.py

import random
from django.utils.crypto import get_random_string
from mango_pests_app.models import Location, MangoThreat, MangoTree, Grower

print("\nStarting combined data population...")

# --------------------------------------
# Get Grower
# --------------------------------------
try:
    grower = Grower.objects.get(user__username='grower')
except Grower.DoesNotExist:
    print("Grower 'grower' not found. Please create the grower with username 'grower' first.")
    exit()

# --------------------------------------
# Create Locations
# --------------------------------------
print("\nCreating Locations...")

location_names = ['Block A', 'Block B', 'Block C']
locations = []

for name in location_names:
    loc, created = Location.objects.get_or_create(
        name=name,
        grower=grower,
        defaults={
            'address': f"{name} Street, MangoVille",
            'description': f"{name} - fertile soil",
            'gps_latitude': round(-12.4 + random.random() * 0.1, 6),
            'gps_longitude': round(130.8 + random.random() * 0.1, 6),
            'area_hectares': random.choice([1.0, 2.5, 3.0]),
            'soil_type': random.choice(['Loam', 'Clay', 'Sandy']),
            'irrigation_type': random.choice(['Drip', 'Sprinkler']),
        }
    )
    locations.append(loc)
    print(f"{'Created' if created else '🔄 Found'} location: {loc.name}")

# --------------------------------------
# Create Mango Threats
# --------------------------------------
print("\nPopulating Mango Threats...")

threats = [
    {'name': 'Anthracnose', 'description': 'Dark leaf/fruit spots', 'threat_type': 'disease', 'risk_level': 'high', 'details': 'Fungal disease'},
    {'name': 'Powdery Mildew', 'description': 'White patches on leaves', 'threat_type': 'disease', 'risk_level': 'moderate', 'details': 'Fungal spores'},
    {'name': 'Fruit Fly', 'description': 'Larvae in fruit', 'threat_type': 'pest', 'risk_level': 'high', 'details': 'Causes internal rotting'},
    {'name': 'Scale Insect', 'description': 'Sap-sucking pest', 'threat_type': 'pest', 'risk_level': 'moderate', 'details': 'Found on bark and stems'},
]

for data in threats:
    threat, created = MangoThreat.objects.get_or_create(name=data['name'], defaults=data)
    if not created:
        for key, value in data.items():
            setattr(threat, key, value)
        threat.save()
    print(f"{'Created' if created else 'Updated'} threat: {threat.name}")

# --------------------------------------
# Create Mango Trees
# --------------------------------------
print("\nPopulating Mango Trees...")

varieties = ['kensington_pride', 'calypso', 'honey_gold', 'r2e2', 'keitt', 'kent']
health_statuses = ['excellent', 'good', 'fair', 'poor']
trees_created = 0

for location in locations:
    for _ in range(10):  # Adjust per location as needed
        tree = MangoTree.objects.create(
            location=location,
            tree_id=f"MANGO-{get_random_string(8)}",
            age=random.randint(1, 20),
            variety=random.choice(varieties),
            height_meters=round(random.uniform(1.5, 5.5), 1),
            canopy_diameter_meters=round(random.uniform(2.0, 6.0), 1),
            health_status=random.choice(health_statuses)
        )
        print(f"Created Tree: {tree.tree_id} → Age {tree.age}, {tree.variety}, Health: {tree.health_status}")
        trees_created += 1

# --------------------------------------
# Summary
# --------------------------------------
print("\nData population complete!")
print(f"Locations created/found: {len(locations)}")
print(f"Threats added/updated: {len(threats)}")
print(f"Total mango trees created: {trees_created}\n")

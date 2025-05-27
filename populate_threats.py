# populate_threats.py
# Create this file in your project root and run: python manage.py shell < populate_threats.py

from mango_pests_app.models import MangoThreat, PlantPart

print("🚀 Populating Mango Threats Database...")

# List of common mango threats
mango_threats_data = [
    # DISEASES
    {
        'name': 'Anthracnose',
        'description': 'Fungal disease causing dark spots on leaves and fruit',
        'threat_type': 'disease',
        'risk_level': 'high',
        'details': 'Anthracnose is a fungal disease that causes dark, sunken lesions on leaves, stems, flowers, and fruits. It thrives in warm, wet conditions and can cause significant crop loss if not controlled.'
    },
    {
        'name': 'Bacterial Black Spot',
        'description': 'Bacterial infection causing black lesions',
        'threat_type': 'disease',
        'risk_level': 'moderate',
        'details': 'Bacterial black spot causes dark brown to black spots with yellow halos on leaves, eventually leading to leaf drop and weakened plant health.'
    },
    {
        'name': 'Mango Scab',
        'description': 'Fungal infection creating rough patches on fruit',
        'threat_type': 'disease',
        'risk_level': 'moderate',
        'details': 'Mango scab causes dark, scabby lesions on young leaves, twigs, and fruit, reducing fruit quality and marketability.'
    },
    {
        'name': 'Powdery Mildew',
        'description': 'White powdery fungal growth on leaves',
        'threat_type': 'disease',
        'risk_level': 'moderate',
        'details': 'Appears as white, powdery spots on leaves and young shoots, can reduce photosynthesis and fruit quality.'
    },
    {
        'name': 'Mango Twig Tip Dieback',
        'description': 'Branches dry and wither from tips',
        'threat_type': 'disease',
        'risk_level': 'high',
        'details': 'Disease causing death of young shoots and impacting overall tree health, common in Northern Territory.'
    },
    {
        'name': 'Mango Malformation',
        'description': 'Abnormal growth of shoots and flowers',
        'threat_type': 'disease',
        'risk_level': 'high',
        'details': 'Causes abnormal growth of flowers and shoots, leading to reduced fruit yield and is under official control.'
    },
    
    # PESTS
    {
        'name': 'Mango Scale',
        'description': 'Small insects that suck sap from trees',
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Scale insects attach to bark, leaves, and fruit, weakening the plant by sucking sap. Heavy infestations can cause yellowing and premature fruit drop.'
    },
    {
        'name': 'Fruit Fly',
        'description': 'Larvae feed inside ripening mango fruit',
        'threat_type': 'pest',
        'risk_level': 'high',
        'details': 'Major pest whose larvae burrow into ripening fruit, causing it to rot from inside and making it unmarketable.'
    },
    {
        'name': 'Mango Leafhopper',
        'description': 'Insects that pierce leaves and transmit diseases',
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Small jumping insects that feed on sap and excrete honeydew, promoting sooty mold growth. Especially damaging during flowering.'
    },
    {
        'name': 'Mango Seed Weevil',
        'description': 'Larvae tunnel through mango seed cavity',  
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Hidden pest that lays eggs on developing fruit, with larvae tunneling into the seed, making it useless and creating quarantine concerns.'
    },
    {
        'name': 'Mango Shoot Borer',
        'description': 'Caterpillars tunnel into young mango shoots',
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Also known as mango tip borer, larvae bore into young shoots causing dieback and potentially reducing fruit production.'
    },
    {
        'name': 'Thrips',
        'description': 'Tiny insects causing silvering damage to leaves',
        'threat_type': 'pest', 
        'risk_level': 'low',
        'details': 'Small insects that scrape leaf surfaces causing silvering damage and can transmit viruses.'
    },
    {
        'name': 'Aphids',
        'description': 'Small soft-bodied insects clustering on new growth',
        'threat_type': 'pest',
        'risk_level': 'low',
        'details': 'Suck plant sap and excrete honeydew, leading to sooty mold. Can curl leaves and stunt growth.'
    },
    {
        'name': 'Mealybugs',
        'description': 'White cottony insects on stems and fruit',
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Covered in white, waxy secretions, they suck sap and excrete honeydew, weakening plants.'
    },
    {
        'name': 'Red Spider Mites',
        'description': 'Tiny mites causing stippling damage to leaves',
        'threat_type': 'pest',
        'risk_level': 'moderate',
        'details': 'Very small mites that cause fine stippling on leaves, can cause severe defoliation in hot, dry conditions.'
    },
    {
        'name': 'Mango Gall Midge',
        'description': 'Larvae form galls on tender plant parts',
        'threat_type': 'pest',
        'risk_level': 'high',
        'details': 'Not currently present in NT but poses biosecurity threat. Causes galls on leaves leading to defoliation.'
    }
]

# Create or update threats
created_count = 0
updated_count = 0

for threat_data in mango_threats_data:
    threat, created = MangoThreat.objects.get_or_create(
        name=threat_data['name'],
        defaults=threat_data
    )
    
    if created:
        created_count += 1
        print(f"✅ Created: {threat.name} ({threat.threat_type}, {threat.risk_level} risk)")
    else:
        # Update existing threat with new data
        for key, value in threat_data.items():
            if key != 'name':  # Don't update the name field
                setattr(threat, key, value)
        threat.save()
        updated_count += 1
        print(f"🔄 Updated: {threat.name} ({threat.threat_type}, {threat.risk_level} risk)")

print(f"\n📊 Summary:")
print(f"✅ Created {created_count} new threats")
print(f"🔄 Updated {updated_count} existing threats")
print(f"📈 Total threats in database: {MangoThreat.objects.count()}")

# Also create plant parts if missing
print(f"\n🌿 Checking Plant Parts...")

plant_parts_data = [
    {'name': 'Leaves', 'description': 'Tree leaves and foliage', 'surveillance_priority': 5, 'time_multiplier': 1.2},
    {'name': 'Fruit', 'description': 'Mango fruit at various stages', 'surveillance_priority': 5, 'time_multiplier': 1.5},
    {'name': 'Branches', 'description': 'Tree branches and stems', 'surveillance_priority': 3, 'time_multiplier': 1.0},
    {'name': 'Trunk', 'description': 'Main tree trunk', 'surveillance_priority': 2, 'time_multiplier': 0.8},
    {'name': 'Root Zone', 'description': 'Area around tree base', 'surveillance_priority': 3, 'time_multiplier': 1.1},
]

plant_parts_created = 0
for part_data in plant_parts_data:
    part, created = PlantPart.objects.get_or_create(
        name=part_data['name'],
        defaults=part_data
    )
    if created:
        plant_parts_created += 1
        print(f"✅ Created plant part: {part.name} (Priority {part.surveillance_priority})")

print(f"✅ Created {plant_parts_created} new plant parts")
print(f"📈 Total plant parts in database: {PlantPart.objects.count()}")

print(f"\n🎉 Database population completed!")
print(f"You should now see threats when creating surveillance records.")
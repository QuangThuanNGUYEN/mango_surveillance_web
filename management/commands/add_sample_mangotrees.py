from django.core.management.base import BaseCommand
from mango_pests_app.models import MangoTree, Location
from django.utils.crypto import get_random_string
import random

class Command(BaseCommand):
    help = "Add 25 sample mango trees to a specified location"

    def handle(self, *args, **kwargs):
        location = Location.objects.first()
        if not location:
            self.stderr.write("❌ No location found. Please create a Location first.")
            return

        varieties = ['kensington_pride', 'calypso', 'honey_gold', 'r2e2', 'keitt', 'kent']
        health_statuses = ['excellent', 'good', 'fair', 'poor']

        for i in range(25):
            tree = MangoTree.objects.create(
                location=location,
                tree_id=f"MANGO-{get_random_string(8)}",
                age=random.randint(1, 20),
                variety=random.choice(varieties),
                height_meters=round(random.uniform(1.5, 5.5), 1),
                canopy_diameter_meters=round(random.uniform(2.0, 6.0), 1),
                health_status=random.choice(health_statuses)
            )
            self.stdout.write(f"✅ Created Mango Tree: {tree.tree_id}")

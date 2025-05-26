from django.contrib import admin
from .models import Grower, Location, MangoTree, MangoThreat, SurveillanceRecord, Inspection

# Register your models here.

admin.site.register(Grower)
admin.site.register(Location)
admin.site.register(MangoTree)
admin.site.register(MangoThreat)
admin.site.register(SurveillanceRecord)
admin.site.register(Inspection)
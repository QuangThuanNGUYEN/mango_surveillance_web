
from django.contrib import admin
from .models import (
    Grower, Location, MangoTree, MangoThreat, SurveillanceRecord, 
    TreeInspection, SurveillancePlan, PlantPart
)


@admin.register(Grower)
class GrowerAdmin(admin.ModelAdmin):
    list_display = ['user', 'farm_name', 'region', 'mango_tree_count', 'stocking_rate']
    list_filter = ['region', 'surveillance_frequency_days']
    search_fields = ['user__username', 'farm_name', 'region']
    readonly_fields = ['user']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'contact_number', 'farm_name', 'region')
        }),
        ('Farm Details', {
            'fields': ('mango_tree_count', 'farm_size_hectares', 'stocking_rate')
        }),
        ('Surveillance Settings', {
            'fields': ('surveillance_frequency_days',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'grower', 'area_hectares', 'get_tree_count']
    list_filter = ['grower', 'soil_type', 'irrigation_type']
    search_fields = ['name', 'address', 'grower__farm_name']
    
    def get_tree_count(self, obj):
        return obj.mango_trees.count()
    get_tree_count.short_description = 'Tree Count'


@admin.register(MangoTree)
class MangoTreeAdmin(admin.ModelAdmin):
    list_display = ['tree_id', 'location', 'variety', 'age', 'age_group', 'health_status']
    list_filter = ['variety', 'age_group', 'health_status', 'location__grower']
    search_fields = ['tree_id', 'location__name', 'location__grower__farm_name']
    readonly_fields = ['age_group']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('location', 'tree_id', 'variety')
        }),
        ('Tree Details', {
            'fields': ('age', 'age_group', 'health_status')
        }),
        ('Physical Characteristics', {
            'fields': ('height_meters', 'canopy_diameter_meters'),
            'classes': ('collapse',)
        })
    )


@admin.register(MangoThreat)
class MangoThreatAdmin(admin.ModelAdmin):
    list_display = ['name', 'threat_type', 'risk_level', 'created_at']
    list_filter = ['threat_type', 'risk_level', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'threat_type', 'risk_level')
        }),
        ('Content', {
            'fields': ('description', 'details', 'image')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SurveillanceRecord)
class SurveillanceRecordAdmin(admin.ModelAdmin):
    list_display = ['grower', 'location', 'date', 'trees_surveyed_count', 'completed']
    list_filter = ['completed', 'date', 'grower', 'location']
    search_fields = ['grower__farm_name', 'location__name', 'notes']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('grower', 'surveillance_plan', 'location', 'date')
        }),
        ('Time Tracking', {
            'fields': ('start_time', 'end_time', 'total_time_minutes')
        }),
        ('Environmental Conditions', {
            'fields': ('weather_conditions', 'temperature_celsius'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('trees_surveyed_count', 'completed', 'notes')
        })
    )


@admin.register(TreeInspection)
class TreeInspectionAdmin(admin.ModelAdmin):
    list_display = ['tree', 'surveillance_record', 'severity_level', 'action_required', 'photo_taken']
    list_filter = ['severity_level', 'action_required', 'photo_taken', 'surveillance_record__date']
    search_fields = ['tree__tree_id', 'findings', 'surveillance_record__grower__farm_name']
    filter_horizontal = ['plant_parts_checked', 'threats_found']


@admin.register(SurveillancePlan)
class SurveillancePlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'grower', 'frequency_days', 'is_active', 'total_estimated_hours']
    list_filter = ['is_active', 'frequency_days', 'created_at']
    search_fields = ['name', 'grower__farm_name']
    filter_horizontal = ['locations', 'target_threats']
    date_hierarchy = 'created_at'


@admin.register(PlantPart)
class PlantPartAdmin(admin.ModelAdmin):
    list_display = ['name', 'surveillance_priority', 'time_multiplier']
    list_filter = ['surveillance_priority']
    search_fields = ['name', 'description']
    ordering = ['-surveillance_priority', 'name']


# Register remaining models with basic admin


# Customize Admin Site Header
admin.site.site_header = "Mango Surveillance Administration"
admin.site.site_title = "Mango Surveillance Admin"
admin.site.index_title = "Welcome to Mango Surveillance Administration"
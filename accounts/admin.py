
# Register your models here.
from django.contrib import admin
from .models import Profile, PetReport

# This allows you to see the Phone Number profiles you created
admin.site.register(Profile)

@admin.register(PetReport)
class PetReportAdmin(admin.ModelAdmin):
    #what admin sees in the list view of the admin panel
    list_display = ('name', 'type', 'report_type', 'status', 'created_at', 'author')

    #allows admin to filter reports based on status and type
    list_filter = ('status', 'report_type', 'created_at')

    #allows admin to search by pet name, type, or location
    search_fields = ('name', 'location', 'breed')
    
    #allows the admin to edit the status of a report direclty from the list vierw
    list_editable = ('status',)



# Register your models here.
from django.contrib import admin
from .models import Profile, PetReport, Pet, ClaimRequest, ClaimMessage, Notification, PetReportLike

# This allows you to see the Phone Number profiles you created
admin.site.register(Profile)

@admin.register(PetReport)
class PetReportAdmin(admin.ModelAdmin):
    #what admin sees in the list view of the admin panel
    list_display = ('name', 'type', 'report_type', 'status', 'created_at', 'author', 'reviewed_by')

    #allows admin to filter reports based on status and type
    list_filter = ('status', 'report_type', 'created_at', 'reviewed_at')

    #allows admin to search by pet name, type, or location
    search_fields = ('name', 'location', 'breed', 'author__username')
    
    #allows the admin to edit the status of a report direclty from the list vierw
    list_editable = ('status',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(report_type__in=['lost', 'found'])


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'user', 'created_at')
    list_filter = ('species', 'created_at')
    search_fields = ('name', 'breed', 'user__username')


@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'claimant', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('claimant__username', 'pet_name', 'report__name', 'report__location')


@admin.register(ClaimMessage)
class ClaimMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'claim', 'sender', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sender__username', 'message')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')


@admin.register(PetReportLike)
class PetReportLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'report', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'report__name', 'report__type', 'report__author__username')


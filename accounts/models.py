from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)

class PetReport(models.Model):
    REPORT_TYPES = [('lost', 'Lost'), ('found', 'Found'), ('text', 'Update'), ('photo', 'Photo')]
    STATUS_CHOICES = [('pending', 'Pending'), ('resolved', 'Resolved'), ('Rejected', 'Rejected')]
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    #Taking pet details
    type = models.CharField(max_length=50) # like dog, cat, cow, donkey, etc
    name = models.CharField(max_length=100, blank=True, null=True)
    breed = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255)
    contact_info = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    #Media and status
    image = models.ImageField(upload_to='pet_reports/', blank=True, null=True)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type} - {self.name or self.type}"
    


from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)


class Pet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=50)
    breed = models.CharField(max_length=100, blank=True)
    age = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    chip = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, default='pet')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.species})"

class PetReport(models.Model):
    REPORT_TYPES = [('lost', 'Lost'), ('found', 'Found'), ('text', 'Update'), ('photo', 'Photo')]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('resolved', 'Resolved'),
    ]
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
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type} - {self.name or self.type}"


class ClaimRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    report = models.ForeignKey(PetReport, on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claim_requests')
    pet_name = models.CharField(max_length=100)
    pet_details = models.TextField()
    proof = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['report', 'claimant'], name='unique_claim_per_report_user')
        ]

    def __str__(self):
        return f"Claim #{self.pk} by {self.claimant.username}"


class ClaimMessage(models.Model):
    claim = models.ForeignKey(ClaimRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claim_messages')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message #{self.pk} for claim #{self.claim_id}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_report = models.ForeignKey(PetReport, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_claim = models.ForeignKey(ClaimRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification #{self.pk} for {self.user.username}"


class PetReportLike(models.Model):
    report = models.ForeignKey(PetReport, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_reports')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['report', 'user'], name='unique_report_like_per_user')
        ]

    def __str__(self):
        return f"Like #{self.pk} on report #{self.report_id} by {self.user.username}"
    


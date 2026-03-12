from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import PetReport


class PetReportApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username='reporter', password='secret123')
		self.client.force_authenticate(user=self.user)

	def test_authenticated_user_can_create_lost_report(self):
		response = self.client.post(
			reverse('pet-report'),
			{
				'report_type': 'lost',
				'type': 'Dog',
				'name': 'Buddy',
				'breed': 'Labrador',
				'color': 'Golden',
				'location': 'Main Street',
				'contact_info': '9999999999',
				'description': 'Seen near the park.',
			},
			format='multipart',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(PetReport.objects.count(), 1)

		report = PetReport.objects.get()
		self.assertEqual(report.author, self.user)
		self.assertEqual(report.report_type, 'lost')
		self.assertEqual(report.status, 'pending')

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import PetReport, Notification


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

	def test_authenticated_user_text_post_is_auto_approved(self):
		response = self.client.post(
			reverse('pet-report'),
			{
				'report_type': 'text',
				'type': 'Dog',
				'name': 'Buddy',
				'description': 'Regular update from home.',
				'location': 'Community Feed',
				'contact_info': 'Not provided',
			},
			format='multipart',
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		report = PetReport.objects.get(report_type='text')
		self.assertEqual(report.status, 'resolved')


class AdminWorkflowTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.admin_user = User.objects.create_user(username='admin1', password='adminpass123', is_staff=True)
		self.normal_user = User.objects.create_user(username='normal1', password='pass12345')

	def test_login_as_admin_requires_staff_user(self):
		response = self.client.post(
			reverse('login'),
			{'username': 'normal1', 'password': 'pass12345', 'admin_login': True},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_admin_can_accept_report_and_user_gets_notification(self):
		report_owner = User.objects.create_user(username='report_owner', password='ownerpass123')
		report = PetReport.objects.create(
			author=report_owner,
			report_type='lost',
			type='Dog',
			name='Milo',
			breed='Mixed',
			color='Brown',
			location='City Park',
			contact_info='1234567890',
			description='Friendly dog',
			status='pending',
		)

		self.client.force_authenticate(user=self.admin_user)
		response = self.client.patch(
			reverse('admin-report-decision', kwargs={'pk': report.id}),
			{'status': 'accepted', 'admin_note': 'Verified details.'},
			format='json',
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		report.refresh_from_db()
		self.assertEqual(report.status, 'accepted')

		notification = Notification.objects.filter(user=report_owner, related_report=report).first()
		self.assertIsNotNone(notification)
		self.assertIn('accepted', notification.message)


class LikePersistenceTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(username='liker', password='likepass123')
		self.client.force_authenticate(user=self.user)
		self.report = PetReport.objects.create(
			author=self.user,
			report_type='text',
			type='Dog',
			name='Rocky',
			location='Community Feed',
			contact_info='Not provided',
			description='Testing likes',
			status='resolved',
		)

	def test_like_toggle_persists_in_reports_list(self):
		response = self.client.post(reverse('pet-report-like-toggle', kwargs={'report_id': self.report.id}))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(response.data['liked'])

		list_response = self.client.get(reverse('pet-report'))
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		item = next((r for r in list_response.data if r['id'] == self.report.id), None)
		self.assertIsNotNone(item)
		self.assertEqual(item['like_count'], 1)
		self.assertTrue(item['liked_by_me'])

from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import ensure_csrf_cookie
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    PetReportSerializer,
    PetSerializer,
    ClaimRequestSerializer,
    ClaimMessageSerializer,
    NotificationSerializer,
)
from .models import PetReport, Pet, ClaimRequest, ClaimMessage, Notification, PetReportLike
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone


# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            admin_login = bool(request.data.get('admin_login'))
            user = authenticate(username=username, password=password)
            if user is not None:
                if admin_login and not (user.is_staff or user.is_superuser):
                    return Response({"message": "This account does not have admin access."}, status=status.HTTP_403_FORBIDDEN)
                # Create a Django session so @login_required-protected pages work.
                django_login(request, user)
                is_admin = user.is_staff or user.is_superuser
                redirect_to = '/accounts/admin-requests/' if admin_login and is_admin else '/accounts/dashboard/'
                return Response(
                    {
                        "message": "Login successful",
                        "is_admin": is_admin,
                        "redirect_to": redirect_to,
                    },
                    status=status.HTTP_200_OK,
                )
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# note to self: this is a protected view that requires authentication. If the user is not authenticated, they will be redirected to the login page.
#we use @login_required so only authenticated users can access the dashboard page.
@ensure_csrf_cookie
@login_required(login_url='/accounts/login-page/')
def dashboard_page(request):
    return render(request, 'dashboard.html')


@login_required(login_url='/accounts/login-page/')
@ensure_csrf_cookie
def user_page(request):
    return render(request, 'user.html')


def _create_notification(user, title, message, report=None, claim=None):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        related_report=report,
        related_claim=claim,
    )


def _is_admin(user):
    return user.is_staff or user.is_superuser


def _admin_users_queryset():
    return User.objects.filter(is_active=True).filter(is_staff=True) | User.objects.filter(is_active=True, is_superuser=True)


class PetReportListCreateView(generics.ListCreateAPIView):
    queryset = PetReport.objects.all().order_by('-created_at')
    serializer_class = PetReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        report_type = serializer.validated_data.get('report_type')
        initial_status = 'pending' if report_type in ['lost', 'found'] else 'resolved'
        serializer.save(author=self.request.user, status=initial_status)


class AdminReportListView(generics.ListAPIView):
    serializer_class = PetReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not _is_admin(self.request.user):
            return PetReport.objects.none()
        queryset = PetReport.objects.filter(report_type__in=['lost', 'found']).order_by('-created_at')
        status_filter = str(self.request.query_params.get('status', '')).strip().lower()
        if status_filter == 'pending':
            queryset = queryset.filter(status='pending')
        return queryset


class AdminReportDecisionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        if not _is_admin(request.user):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        report = PetReport.objects.filter(pk=pk, report_type__in=['lost', 'found']).first()
        if not report:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        decision = str(request.data.get('status', '')).strip().lower()
        note = str(request.data.get('admin_note', '')).strip()
        if decision not in ['accepted', 'rejected']:
            return Response({"detail": "status must be accepted or rejected."}, status=status.HTTP_400_BAD_REQUEST)

        report.status = decision
        report.admin_note = note
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.save(update_fields=['status', 'admin_note', 'reviewed_by', 'reviewed_at'])

        outcome = 'accepted' if decision == 'accepted' else 'rejected'
        text = f"Your {report.report_type} report has been {outcome} by admin."
        if note:
            text = f"{text} Note: {note}"
        _create_notification(report.author, 'Report Update', text, report=report)

        return Response(PetReportSerializer(report).data, status=status.HTTP_200_OK)


class PetListCreateView(generics.ListCreateAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pet.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pet.objects.filter(user=self.request.user)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        notification = Notification.objects.filter(pk=pk, user=request.user).first()
        if not notification:
            return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)


class NotificationBulkActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        action = str(request.data.get('action', '')).strip().lower()
        if action not in ['mark_read', 'mark_unread']:
            return Response({"detail": "action must be mark_read or mark_unread."}, status=status.HTTP_400_BAD_REQUEST)

        notifications = Notification.objects.filter(user=request.user)
        ids = request.data.get('notification_ids')
        if isinstance(ids, list) and ids:
            notifications = notifications.filter(id__in=ids)

        is_read = action == 'mark_read'
        updated = notifications.update(is_read=is_read)
        return Response({"updated": updated, "is_read": is_read}, status=status.HTTP_200_OK)


class ClaimRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = ClaimRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if _is_admin(user):
            queryset = ClaimRequest.objects.select_related('report', 'claimant', 'report__author').all().order_by('-created_at')
            status_filter = str(self.request.query_params.get('status', '')).strip().lower()
            if status_filter == 'pending':
                queryset = queryset.filter(status='pending')
            return queryset
        return ClaimRequest.objects.select_related('report', 'claimant', 'report__author').filter(claimant=user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code != status.HTTP_201_CREATED:
            return response

        claim = ClaimRequest.objects.select_related('report').get(pk=response.data['id'])
        initial_message = str(request.data.get('initial_message', '')).strip()
        if initial_message:
            ClaimMessage.objects.create(claim=claim, sender=request.user, message=initial_message)

        admins = _admin_users_queryset().distinct()
        for admin in admins:
            _create_notification(
                admin,
                'New Claim Request',
                f"{request.user.username} raised a claim on report #{claim.report_id}.",
                report=claim.report,
                claim=claim,
            )

        return response

    def perform_create(self, serializer):
        report = serializer.validated_data['report']
        if report.author_id == self.request.user.id:
            raise PermissionDenied('You cannot claim your own report.')
        serializer.save(claimant=self.request.user)


class ClaimMessageListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _can_access(self, user, claim):
        return _is_admin(user) or claim.claimant_id == user.id

    def get(self, request, claim_id):
        claim = ClaimRequest.objects.filter(pk=claim_id).first()
        if not claim:
            return Response({"detail": "Claim not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_access(request.user, claim):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        messages = ClaimMessage.objects.filter(claim=claim).select_related('sender')
        return Response(ClaimMessageSerializer(messages, many=True).data, status=status.HTTP_200_OK)

    def post(self, request, claim_id):
        claim = ClaimRequest.objects.select_related('report', 'claimant').filter(pk=claim_id).first()
        if not claim:
            return Response({"detail": "Claim not found."}, status=status.HTTP_404_NOT_FOUND)
        if not self._can_access(request.user, claim):
            return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

        message = str(request.data.get('message', '')).strip()
        if not message:
            return Response({"detail": "message is required."}, status=status.HTTP_400_BAD_REQUEST)

        created = ClaimMessage.objects.create(claim=claim, sender=request.user, message=message)

        if _is_admin(request.user):
            _create_notification(
                claim.claimant,
                'Admin Message',
                f"Admin replied on your claim #{claim.id}.",
                report=claim.report,
                claim=claim,
            )
        else:
            admins = _admin_users_queryset()
            for admin in admins.distinct():
                _create_notification(
                    admin,
                    'Claim Message',
                    f"New message from {request.user.username} on claim #{claim.id}.",
                    report=claim.report,
                    claim=claim,
                )

        return Response(ClaimMessageSerializer(created).data, status=status.HTTP_201_CREATED)


class AdminClaimDecisionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, claim_id):
        if not _is_admin(request.user):
            return Response({"detail": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        claim = ClaimRequest.objects.select_related('report', 'claimant').filter(pk=claim_id).first()
        if not claim:
            return Response({"detail": "Claim not found."}, status=status.HTTP_404_NOT_FOUND)

        decision = str(request.data.get('status', '')).strip().lower()
        admin_reply = str(request.data.get('admin_reply', '')).strip()
        if decision not in ['accepted', 'rejected']:
            return Response({"detail": "status must be accepted or rejected."}, status=status.HTTP_400_BAD_REQUEST)

        claim.status = decision
        if admin_reply:
            claim.admin_reply = admin_reply
        claim.save(update_fields=['status', 'admin_reply', 'updated_at'])

        if admin_reply:
            ClaimMessage.objects.create(claim=claim, sender=request.user, message=admin_reply)

        outcome = 'accepted' if decision == 'accepted' else 'rejected'
        text = f"Your claim #{claim.id} has been {outcome} by admin."
        if admin_reply:
            text = f"{text} Message: {admin_reply}"
        _create_notification(claim.claimant, 'Claim Update', text, report=claim.report, claim=claim)

        return Response(ClaimRequestSerializer(claim).data, status=status.HTTP_200_OK)


class PetReportLikeToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, report_id):
        report = PetReport.objects.filter(pk=report_id).first()
        if not report:
            return Response({"detail": "Report not found."}, status=status.HTTP_404_NOT_FOUND)

        like = PetReportLike.objects.filter(report=report, user=request.user).first()
        if like:
            like.delete()
            liked = False
        else:
            PetReportLike.objects.create(report=report, user=request.user)
            liked = True

        return Response(
            {
                "liked": liked,
                "like_count": report.likes.count(),
                "report_id": report.id,
            },
            status=status.HTTP_200_OK,
        )







#frontend code for login and registration
def register_page(request):
    return render(request, 'register.html')

def login_page(request):
    return render(request, 'login.html')


@ensure_csrf_cookie
@login_required(login_url='/accounts/login-page/')
@user_passes_test(_is_admin)
def admin_requests_page(request):
    return render(request, 'admin_requests.html')




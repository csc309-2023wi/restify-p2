from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    CurrentUserDefault,
)
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from datetime import date
from django.db.models import Q
from ..models import User, Property, Reservation, Notification


class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "user_id",
            "reservation_id",
            "property_id",
            "content",
            "is_read",
            "is_cleared",
            "created_at",
            "is_cancel_req",
        ]
        fields = ["id", "user_id", "reservation_id", "property_id", "content"]


class NotificationPagination(PageNumberPagination):
    page_size = 5


class NotificationsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = NotificationPagination

    def get_queryset(self):
        print("A")
        user_id = self.request.user.id
        print("B")
        user = get_object_or_404(User, id=user_id)
        print("C")
        query_set = Notification.objects.filter(user_id=user, is_cleared=False)
        print("D")
        return query_set


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get(self, request, id):
        notification = get_object_or_404(Notification, id=self.kwargs.get("id"))
        user = get_object_or_404(User, id=self.request.user.id)
        if notification.user_id != user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if notification.is_cleared:
            return Response(status=status.HTTP_403_FORBIDDEN)
        notification.is_read = True
        notification.is_cleared = True
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (
    ModelSerializer,
)
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from ..models import User

class UserCreateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
            "password",
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        new_user = User(**validated_data)
        new_user.set_password(password)
        new_user.save()
        return new_user

class UserUpdateSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
            "password",
        ]

class SignUpView(CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()

class ProfileView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = (IsAuthenticated,)
    def get_object(self):
        return self.request.user
    
    def get(self, request):
        serializer = UserUpdateSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


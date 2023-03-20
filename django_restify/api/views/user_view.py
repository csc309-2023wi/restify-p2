from rest_framework.generics import CreateAPIView, UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    ValidationError,
)
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from ..models import User


class UserCreateSerializer(ModelSerializer):
    password2 = CharField(write_only=True, required=True)

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
            "password2",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise ValidationError(
                {"error": "Passwords do not match."}, code=status.HTTP_400_BAD_REQUEST
            )
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        new_user = User(**validated_data)
        new_user.set_password(password)
        new_user.save()
        return new_user


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "avatar",
        ]


class ProfileUpdateSerializer(ModelSerializer):
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


class SignUpView(CreateAPIView):
    serializer_class = UserCreateSerializer
    queryset = User.objects.all()


class ProfileView(RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(request.user, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            data = serializer.data
            self.object.set_password(serializer.data.get("password"))
            self.object.save()
            data.pop("password")
            return Response(data, status=status.HTTP_200_OK)

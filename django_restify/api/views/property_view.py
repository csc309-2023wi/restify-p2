from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    CurrentUserDefault,
)
from rest_framework import permissions

from ..models import User, Property


class PropertySerializer(ModelSerializer):
    host_id = PrimaryKeyRelatedField(
        source="host.id", many=False, default=CurrentUserDefault(), read_only=True
    )

    class Meta:
        model = Property
        fields = [
            "id",
            "host_id",
            "address",
            "description",
            "guest_capacity",
            "availability",
            "amenities",
            "images",
        ]


class PropertyListCreateView(ListCreateAPIView):
    serializer_class = PropertySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        queryset = Property.objects.all()
        host_id = self.request.query_params.get("host_id")
        if host_id is not None:
            queryset = queryset.filter(host__id=host_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(host=self.request.user)


class PropertyRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

from random import randrange
from django.db.models import F, Q, Value, Min, DateField
from django.db.models.functions import Cast
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
    IntegerField,
    CurrentUserDefault,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters, permissions
from functools import reduce
from operator import and_

from ..models import Property
from .image_view import image_save


class PropertySerializer(ModelSerializer):
    host_id = PrimaryKeyRelatedField(
        source="host.id", many=False, default=CurrentUserDefault(), read_only=True
    )
    images = SerializerMethodField()
    rating = IntegerField(read_only=True)

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
            "rating",
        ]

    def get_images(self, obj):
        return [image.h for image in obj.images.all()]


class PropertyPagination(PageNumberPagination):
    page_size = 9
    page_size_query_param = "page_size"
    max_page_size = 36


class PropertyListCreateView(ListCreateAPIView):
    serializer_class = PropertySerializer
    pagination_class = PropertyPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["address", "description", "amenities"]
    ordering_fields = ["rating", "earliest_availability"]

    def get_queryset(self):
        """
        This view should return a list of all the purchases for
        the user as determined by the username portion of the URL.
        """
        queryset = Property.objects.order_by("id")

        # GET query parameters

        host_id = self.request.query_params.get("host_id")
        if host_id is not None:
            queryset = queryset.filter(host__id=host_id)

        location = self.request.query_params.get("location")
        if location is not None:
            queryset = queryset.filter(address__icontains=location)

        num_guests = self.request.query_params.get("num_guests")
        if num_guests is not None:
            queryset = queryset.filter(guest_capacity__gte=num_guests)

        amenities_q = self.request.query_params.get("amenities")
        if amenities_q is not None:
            # Split query param into list of amenities
            amenities = amenities_q.split(",")
            queryset = queryset.filter(
                reduce(
                    and_,
                    (Q(amenities__icontains=term) for term in amenities),
                )
            )

        # annotate rating
        queryset = queryset.annotate(rating=F("id") + Value(randrange(1, 6)))

        # annotate earliest start date
        queryset = queryset.annotate(
            earliest_availability=Min(
                Cast(F("availability__0__from"), output_field=DateField())
            )
        )

        return queryset

    def perform_create(self, serializer):
        images = self.request.data.get("images", [])
        image_objs = []
        for image in images:
            ext = image.get("ext", None)
            data = image.get("data", None)
            if ext and data:
                image_obj = image_save(data, ext)
                image_objs.append(image_obj)
        serializer.save(host=self.request.user, images=image_objs)


class PropertyRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    lookup_field = "id"
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def perform_update(self, serializer):
        instance = serializer.save()

        image_ops = self.request.data.get("image_ops", {})
        delete_hashes = image_ops.get("delete", [])
        add_images = image_ops.get("add", [])

        for delete_hash in delete_hashes:
            if delete_hash not in set(instance.images.values_list("h", flat=True)):
                raise PermissionDenied(
                    "Cannot delete image that does not belong to this property."
                )
            instance.images.get(h=delete_hash).delete()

        for image_obj in add_images:
            ext = image_obj.get("ext", None)
            data = image_obj.get("data", None)
            if ext and data:
                image = image_save(data, ext)
                instance.images.add(image)

from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    CurrentUserDefault,
)
from rest_framework import permissions
from datetime import date
from django.db.models import Q
from ..models import User, Property, Reservation, Notification


class ReservationSerializer(ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "guest_id",
            "property_id",
            "status",
            "guest_count",
            "from_date",
            "to_date",
        ]
        read_only_fields = ["status", "guest_id"]
        # read_only_fields = ["status", "property_id", "guest_id"]


class ReservationHostSerializer(ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "id",
            "guest_id",
            "property_id",
            "status",
            "guest_count",
            "from_date",
            "to_date",
        ]
        read_only_fields = [
            "id",
            "property_id",
            "guest_id",
            "guest_count",
            "from_date",
            "to_date",
        ]


class ReservationPagination(PageNumberPagination):
    page_size = 5


class ReservationListView(ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReservationPagination

    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get("type")
        if user_type != "host" and user_type != "guest":
            return Response(
                {"error": "Invalid Query Paramater - type"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Reservation.objects.all()
        user_type = self.request.query_params.get("type")
        host_id = self.request.user.id

        if user_type == "host":
            queryset = queryset.filter(property__host__id=host_id)
        elif user_type == "guest":
            user = get_object_or_404(User, id=host_id)
            queryset = user.reservations_outgoing.all()
        else:
            queryset = Reservation.objects.filter(guest_count__lte=0)

        state = self.request.query_params.get("status")
        if state is not None:
            queryset = queryset.filter(status=state)

        for reservation in queryset:
            start_date = reservation.from_date
            end_date = reservation.to_date
            if reservation.status == "PE" and start_date < date.today():
                reservation.status = "EX"
                reservation.save()
            if reservation.status == "AP" and end_date < date.today():
                reservation.status = "CO"
                reservation.save()
        return queryset


class ReservationCreateView(CreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def perform_create(self, serializer):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data["from_date"]
        end_date = serializer.validated_data["to_date"]
        property_id = serializer.validated_data["property_id"]
        property = property_id
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if start_date > end_date:
            return Response(
                {"error": "Start date must be before end date!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if start_date < date.today():
            return Response(
                {"error": "Start date must be in the future!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        conflicts = Reservation.objects.filter(
            Q(property_id=property.id),
            Q(from_date__lte=end_date, to_date__gte=start_date),
            Q(status="AP"),
        )
        if conflicts:
            return Response(
                {"error": "This property is unavailable during the request time period!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save(status="PE", guest_id=user)

        notification = Notification.objects.create(
            user_id=property.host,
            reservation_id=serializer.instance,
            property_id=property,
            content=f"{user.username} has requested to reserve the property {property.address} from {start_date} to {end_date}.",
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReservationUpdateView(UpdateAPIView):
    queryset = Reservation.objects.filter(status="PE")
    serializer_class = ReservationHostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get("pk"))
        property = reservation.property_id
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if user != property.host:
            return Response(
                {"error": "Only the host is authorized to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if reservation.status != "PE":
            return Response(
                {"error": "This reservation is not in the pending state"},
                status=status.HTTP_403_FORBIDDEN,
            )

        state = request.data.get("status")
        if state not in ("AP", "DE"):
            if state is None:
                return Response(
                    {"error": "Status is required."}, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {"error": "Invalid status. Reservation must be approved or denied."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if state == "AP":
            for res in Reservation.objects.filter(property_id=property.id, status="AP"):
                if (
                    res.from_date <= reservation.to_date
                    and res.to_date >= reservation.from_date
                ):
                    return Response(
                        {
                            "error": "This property already has an approved reservation overlapping with these dates"
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

        reservation.status = state
        reservation.save()
        serializer = self.serializer_class(reservation)
        if state == "AP":
            # for res in Reservation.objects.filter(property_id = property.id, status='PE'):
            #     if res.from_date <= reservation.to_date or res.to_date >= reservation.from_date:
            #         res.status = 'DE'
            #         res.save()
            notification = Notification.objects.create(
                user_id=reservation.guest_id,
                reservation_id=reservation,
                property_id=property,
                content=f"Your reservation request for {property.address} from {reservation.from_date} to {reservation.to_date} has been approved.",
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReservationCancelView(APIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get("pk"))
        property = reservation.property_id
        serializer = ReservationSerializer(reservation)
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if reservation.guest_id != user:
            return Response(
                {"error": "You do not have permission to cancel this reservation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if reservation.status not in ("Pending", "PE", "AP", "Approved"):
            return Response(
                {"error": "This reservation is not in a cancellable state."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if reservation.status == "PE":
            reservation.status = "CA"
            reservation.save()
            dict = serializer.data
            dict["Message"] = "Reservation has been cancelled"
            return Response(dict, status=status.HTTP_200_OK)
        else:
            reservation.status = "PC"
            reservation.save()

            notification = Notification.objects.create(
                user_id=property.host,
                reservation_id=reservation,
                property_id=property,
                is_cancel_req=True,
                content=f"{user.username} has requested to cancel their reservation of the property {property.address}",
            )
            dict = serializer.data
            dict["Message"] = "Request for cancellation has been sent to host"
            return Response(dict, status=status.HTTP_200_OK)


class ReservationHostCancelView(APIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get("pk"))
        property = reservation.property_id
        serializer = ReservationSerializer(reservation)
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)
        cancel = self.request.query_params.get("cancel")

        if property.host != user:
            return Response(
                {"error": "You do not have permission to cancel this reservation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if reservation.status != "AP" and reservation.status != "PC":
            return Response(
                {"error": "This reservation is not in a cancellable state."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if cancel is None or reservation.status == "AP":
            reservation.status = "TE"
            reservation.save()
            dict = serializer.data
            dict["Message"] = "Reservation has been Terminated"
            return Response(dict, status=status.HTTP_200_OK)
        elif cancel != "true" and cancel != "false":
            return Response(
                {"error": "Invalid cancel value. Cancel must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        elif cancel == "false":
            reservation.status = "AP"
            reservation.save()
            dict = serializer.data
            dict["Message"] = "Cancellation request has been denied"
            return Response(dict, status=status.HTTP_200_OK)
        else:
            reservation.status = "CA"
            reservation.save()
            dict = serializer.data
            dict["Message"] = "Reservation has been cancelled"

            notification = Notification.objects.create(
                user_id=reservation.guest_id,
                reservation_id=reservation,
                property_id=property,
                content=f"You request to cancel the reservation of the property {property.address} has been approved.",
            )
            return Response(dict, status=status.HTTP_200_OK)

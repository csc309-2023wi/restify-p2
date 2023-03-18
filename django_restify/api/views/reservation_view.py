from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, RetrieveUpdateDestroyAPIView
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
            "guest",
            "property",
            "status",
            "guest_count",
            "from_date",
            "to_date",
        ]
        read_only_fields = ["status", "property", "guest"]

class ReservationHostSerializer(ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            "guest",
            "property",
            "status",
            "guest_count",
            "from_date",
            "to_date",
        ]
        read_only_fields = ["property", "guest", "guest_count", "from_date", "to_date"]

class ReservationPagination(PageNumberPagination):
    page_size = 5

class ReservationListView(ListAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ReservationPagination

    def get(self, request, *args, **kwargs):
        user_type = self.request.query_params.get('type')
        if user_type != 'host' and user_type != 'guest':
            return Response({'error': 'Invalid Query Paramater - type'}, status=status.HTTP_400_BAD_REQUEST)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Reservation.objects.all()
        user_type = self.request.query_params.get('type')
        host_id = self.request.user.id

        if user_type == 'host':
            queryset = queryset.filter(property__host__id=host_id)
        elif user_type == 'guest':
            user = get_object_or_404(User, id=host_id)
            queryset = user.reservations_outgoing.all()
        else:
            queryset = Reservation.objects.filter(guest_count__lte=0)
        
        state = self.request.query_params.get('status')
        if state is not None:
            queryset = queryset.filter(status=state)
        
        return queryset

class ReservationCreateView(CreateAPIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    # def perform_create(self, serializer):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  

        start_date = serializer.validated_data['from_date']
        end_date = serializer.validated_data['to_date']
        property = get_object_or_404(Property, id=self.kwargs['pk'])
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if start_date > end_date:
            return Response({'error': 'Start date must be before end date!'}, status=status.HTTP_403_FORBIDDEN)
        
        if start_date < date.today():
            return Response({'error': 'Start date must be in the future!'}, status=status.HTTP_403_FORBIDDEN)

        conflicts = Reservation.objects.filter(
            Q(property_id = property.id),
            Q(from_date__lte=end_date, to_date__gte=start_date),
            Q(status='AP')
        )
        if conflicts:
            return Response({'error': 'This property is unavailable during the request time period!'}, status=status.HTTP_403_FORBIDDEN)

        serializer.save(status="PE", property=property, guest=user)

        notification = Notification.objects.create(
            user = property.host,
            reservation = serializer.instance,
            content=f"{user.username} has requested to reserve the property {property.address} from {start_date} to {end_date}."
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ReservationUpdateView(UpdateAPIView):
    queryset = Reservation.objects.filter(status='PE')
    serializer_class = ReservationHostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get('pk'))
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if user != reservation.property.host or reservation.status != 'PE':
            return Response({'error': 'You are not authorized to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        state = request.data.get('status')
        if state not in ('AP', 'DE'):
            return Response({'error': 'Invalid status. Reservation must be approved or denied.'}, status=status.HTTP_400_BAD_REQUEST)
        
        reservation.status = state
        reservation.save()
        serializer = self.serializer_class(reservation)
        if state == 'AP':
            for res in Reservation.objects.filter(property_id = reservation.property.id, status='PE'):
                if res.from_date <= reservation.to_date or res.to_date >= reservation.from_date:
                    res.status = 'DE'
                    res.save()
            notification = Notification.objects.create(
                user = reservation.guest,
                reservation = reservation,
                content=f"Your reservation request for {reservation.property.address} from {reservation.from_date} to {reservation.to_date} has been approved."
            )
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class ReservationCancelView(APIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get('pk'))
        serializer = ReservationSerializer(reservation)
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if reservation.guest != user:
            return Response(
                {'error': 'You do not have permission to cancel this reservation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if reservation.status not in ('Pending', 'PE', 'AP', 'Approved'):
            return Response(
                {'error': 'This reservation is not in a cancellable state.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if reservation.status == 'PE':
            reservation.status = 'CA'
            reservation.save()
            dict = serializer.data
            dict['Message'] = 'Reservation has been cancelled'
            return Response(dict, status=status.HTTP_200_OK)
        else:
            reservation.status = 'PC'
            reservation.save()

            notification = Notification.objects.create(
            user = reservation.property.host,
            reservation=reservation,
            is_cancel_req=True,
            content=f"{user.username} has requested to cancel their reservation of the property {reservation.property.address}"
            )
            dict = serializer.data
            dict['Message'] = 'Request for cancellation has been sent to host'
            return Response(dict, status=status.HTTP_200_OK)

class ReservationHostCancelView(APIView):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        reservation = get_object_or_404(Reservation, id=self.kwargs.get('pk'))
        serializer = ReservationSerializer(reservation)
        user_id = self.request.user.id
        user = get_object_or_404(User, id=user_id)

        if reservation.property.host != user:
            return Response(
                {'error': 'You do not have permission to cancel this reservation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if reservation.status != 'AP' and reservation.status != 'PC':
            return Response(
                {'error': 'This reservation is not in a cancellable state.'},
                status=status.HTTP_403_FORBIDDEN

            )
        
        if  reservation.status == 'PC':
            reservation.status = 'CA'
            reservation.save()
            dict = serializer.data
            dict['Message'] = 'Reservation has been cancelled'

            notification = Notification.objects.create(
            user = reservation.guest,
            reservation=reservation,
            content=f"You request to cancel the reservation of the property {reservation.property.address} has been approved.")
            return Response(dict, status=status.HTTP_200_OK)
        else:
            reservation.status = 'TE'
            reservation.save()
            dict = serializer.data
            dict['Message'] = 'Reservation has been Terminated'
            return Response(dict, status=status.HTTP_200_OK)
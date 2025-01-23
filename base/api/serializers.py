from rest_framework.serializers import ModelSerializer, SerializerMethodField
from base import models
from datetime import datetime, timedelta
from django.utils import timezone


class UserSerializer(ModelSerializer):
    class Meta:
        model = models.User
        exclude = ['password']


class UserListSerializer(ModelSerializer):
    class Meta:
        model = models.User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar']


class LocationSerializer(ModelSerializer):
    class Meta:
        model = models.Location
        fields = '__all__'


class ChatRoomSerializer(ModelSerializer):
    users = SerializerMethodField()
    active_info = SerializerMethodField()
    
    def get_users(self, obj):
        return UserListSerializer(
            obj.users.all(),
            context={'request': self.context['request']},
            many=True
        ).data
    
    def get_active_info(self, obj):
        last_seen = models.LastSeen.objects.filter(
            user=self.context['request'].user, room=obj).first()
        messages = obj.messages.all().order_by('-date')
        last_message = messages.first()
        return {
            'last_seen': last_seen.date if last_seen else None,
            'last_message': MessageSerializer(
                last_message,
                context={'request': self.context['request']},
                many=False
            ).data if last_message else None,
            'n_new_messages': messages.filter(
                date__gt=last_seen.date,
            ).exclude(
                sender=self.context['request'].user
            ).count() if last_seen else messages.exclude(sender=self.context['request'].user).count()
        }
    
    class Meta:
        model = models.ChatRoom
        fields = '__all__'


class MessageSerializer(ModelSerializer):
    class Meta:
        model = models.Message
        fields = '__all__'


class CourseSerializer(ModelSerializer):
    trainer = UserSerializer(read_only=True)
    weekly_sessions = SerializerMethodField()
    location = LocationSerializer(read_only=True)

    def get_weekly_sessions(self, obj):
        # Get sessions in this week
        today = timezone.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        return TrainingSessionSerializer(
            obj.training_sessions.filter(
                start__gte=start_of_week,
                start__lte=end_of_week
            ),
            context={'request': self.context['request']},
            many=True
        ).data
    
    class Meta:
        model = models.Course
        fields = '__all__'


class MinimalCourseSerializer(ModelSerializer):
    # trainer = SerializerMethodField()
    location = SerializerMethodField()

    # def get_trainer(self, obj):
    #     return obj.trainer.username

    def get_location(self, obj):
        return obj.location.name

    class Meta:
        model = models.Course
        fields = ['id', 'title', 'location', 'sport', 'unit_price', 'unit_session', 'max_trainee']


class BookingSessionSerializer(ModelSerializer):
    course = MinimalCourseSerializer(read_only=True)
    n_members = SerializerMethodField()
    is_booked = SerializerMethodField()
    user = UserListSerializer(read_only=True)

    def get_n_members(self, obj):
        if obj.training_session:
            return obj.training_session.booking_sessions.count()
        return 0

    def get_is_booked(self, obj):
        # is_booked sẽ là true nếu người dùng booking thành công và training_session khác null
        return obj.training_session is not None and obj.user == self.context['request'].user

    class Meta:
        model = models.BookingSession
        fields = '__all__'


class TrainingSessionSerializer(ModelSerializer):
    course = MinimalCourseSerializer(read_only=True)
    n_members = SerializerMethodField()
    is_booked = SerializerMethodField()
    price = SerializerMethodField()

    def get_n_members(self, obj):
        return obj.booking_sessions.count()

    def get_price(self, obj):
        price = sum(booking_session.price for booking_session in obj.booking_sessions.all())
        return price

    def get_is_booked(self, obj):
        # Kiểm tra nếu có bất kỳ booking_session nào của người dùng trỏ đến training_session
        user = self.context['request'].user
        if obj.course.trainer == user:
            return obj.booking_sessions.count() > 0
        return obj.booking_sessions.filter(user=self.context['request'].user).exists()

    class Meta:
        model = models.TrainingSession
        fields = '__all__'


class TrainingSessionDetailSerializer(TrainingSessionSerializer):
    course = CourseSerializer(read_only=True)
    booking_sessions = BookingSessionSerializer(many=True, read_only=True)

    class Meta:
        model = models.TrainingSession
        fields = '__all__'


class PaymentSerializer(ModelSerializer):
    sender = SerializerMethodField()
    receiver = SerializerMethodField()
    booking_sessions = BookingSessionSerializer(many=True, read_only=True)
    
    def get_sender(self, obj):
        return obj.sender.username
    
    def get_receiver(self, obj):
        return obj.receiver.username
    
    class Meta:
        model = models.Payment
        fields = '__all__'
        depth = 1  # Để lấy thêm thông tin chi tiết của các related fields


class RatingSerializer(ModelSerializer):
    class Meta:
        model = models.Rating
        fields = '__all__'

from datetime import timezone

from rest_framework import serializers
from .models import User, Book, Order, UserRole, OrderStatus
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_role(self, value):
        if value not in [UserRole.ADMIN, UserRole.OPERATOR, UserRole.USER]:
            raise serializers.ValidationError("Invalid role. Must be 'admin', 'operator', or 'user'.")
        return value

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            role=validated_data['role']
        )
        user.set_password(validated_data['password'])  
        user.save()
        print(f"User created: {user.username}, hashed password: {user.password}")  
        return user

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'quantity']

class OrderCreateSerializer(serializers.ModelSerializer):
    book_id = serializers.IntegerField(write_only=True)  

    class Meta:
        model = Order
        fields = ['book_id']  

    def validate_book_id(self, value):
        if not Book.objects.filter(id=value).exists():
            raise serializers.ValidationError("Book does not exist")
        return value

    def create(self, validated_data):
        book_id = validated_data.pop('book_id')
        book = Book.objects.get(id=book_id)
        user = self.context['request'].user
        order = Order.objects.create(
            user=user,
            book=book,
            order_date=timezone.now(),
            status=OrderStatus.BOOKED.value
        )
        return order

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'book', 'user', 'order_date', 'status', 'taken_at', 'returned_at', 'penalty', 'rating']


class OrderAddRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=0, max_value=5)


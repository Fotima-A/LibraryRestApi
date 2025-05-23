from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import authenticate
from .serializers import UserCreateSerializer, UserSerializer, BookSerializer, OrderSerializer
from .permissions import RoleBasedPermission
from .models import UserRole, Book, Order, User
from datetime import timedelta
from django.utils import timezone

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            required=['username', 'password']
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                    'access': openapi.Schema(type=openapi.TYPE_STRING),
                    'token_type': openapi.Schema(type=openapi.TYPE_STRING),
                }
            ),
            401: 'Unauthorized'
        },
        security=[],
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"detail": "Incorrect username or password"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "token_type": "bearer"
        })

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, description='Role (admin, operator, or user)', enum=['admin', 'operator', 'user']),
            },
            required=['username', 'password', 'role']
        ),
        responses={
            201: UserSerializer,
            400: 'Bad Request'
        },
        security=[],
    )
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            if User.objects.filter(username=serializer.validated_data['username']).exists():
                return Response({"detail": "Username already registered"}, status=status.HTTP_400_BAD_REQUEST)
            user = serializer.create(serializer.validated_data)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]  
        return [RoleBasedPermission(allowed_roles=[UserRole.ADMIN, UserRole.OPERATOR])]  

    @swagger_auto_schema(
        operation_description="Get list of books (accessible to all authenticated users)",
        responses={200: BookSerializer(many=True)},
        security=[{'Bearer': []}],
    )
    def get(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new book (Admin and Operator only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Book title'),
                'author': openapi.Schema(type=openapi.TYPE_STRING, description='Book author'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity of books'),
            },
            required=['title', 'author', 'quantity']
        ),
        responses={201: BookSerializer},
        security=[{'Bearer': []}],
    )
    def post(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookUpdateDeleteView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.ADMIN, UserRole.OPERATOR])]  

    @swagger_auto_schema(
        operation_description="Update a book (Admin and Operator only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Book title'),
                'author': openapi.Schema(type=openapi.TYPE_STRING, description='Book author'),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Quantity of books'),
            },
            required=['title', 'author', 'quantity']
        ),
        responses={200: BookSerializer},
        security=[{'Bearer': []}],
    )
    def put(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookSerializer(book, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a book (Admin and Operator only)",
        responses={204: 'Book deleted'},
        security=[{'Bearer': []}],
    )
    def delete(self, request, book_id):
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        book.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrderCreateView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.USER])]  

    @swagger_auto_schema(
        operation_description="Reserve a book (User only, auto-cancels after 1 day if not picked up)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'book_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Book ID to reserve'),
            },
            required=['book_id']
        ),
        responses={201: OrderSerializer},
        security=[{'Bearer': []}],
    )
    def post(self, request):
        book_id = request.data.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.quantity <= 0:
            return Response({"detail": "Book is not available"}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user, book=book)
        book.quantity -= 1
        book.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderListView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.ADMIN, UserRole.OPERATOR])]  

    @swagger_auto_schema(
        operation_description="View all orders with details (Admin and Operator only)",
        responses={200: OrderSerializer(many=True)},
        security=[{'Bearer': []}],
    )
    def get(self, request):
        orders = Order.objects.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class OrderAcceptView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.ADMIN, UserRole.OPERATOR])]  

    @swagger_auto_schema(
        operation_description="Accept an order (Admin and Operator only)",
        responses={200: OrderSerializer},
        security=[{'Bearer': []}],
    )
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if order.picked_up_at:
            return Response({"detail": "Order already accepted"}, status=status.HTTP_400_BAD_REQUEST)

        order.picked_up_at = timezone.now()
        order.save()
        return Response(OrderSerializer(order).data)

class OrderReturnView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.ADMIN, UserRole.OPERATOR])]  

    @swagger_auto_schema(
        operation_description="Return an order (Admin and Operator only)",
        responses={200: OrderSerializer},
        security=[{'Bearer': []}],
    )
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if not order.picked_up_at:
            return Response({"detail": "Order not yet accepted"}, status=status.HTTP_400_BAD_REQUEST)

        if order.returned_at:
            return Response({"detail": "Order already returned"}, status=status.HTTP_400_BAD_REQUEST)

        order.returned_at = timezone.now()
        order.book.quantity += 1
        order.book.save()
        order.save()
        return Response(OrderSerializer(order).data)

class OrderRateView(APIView):
    permission_classes = [RoleBasedPermission(allowed_roles=[UserRole.USER])]  

    @swagger_auto_schema(
        operation_description="Rate a book after reading (User only, 0-5 stars)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, description='Rating (0-5)', minimum=0, maximum=5),
            },
            required=['rating']
        ),
        responses={200: 'Rating submitted'},
        security=[{'Bearer': []}],
    )
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        if not order.returned_at:
            return Response({"detail": "Order not yet returned"}, status=status.HTTP_400_BAD_REQUEST)

        rating = request.data.get('rating')
        if not isinstance(rating, int) or rating < 0 or rating > 5:
            return Response({"detail": "Rating must be between 0 and 5"}, status=status.HTTP_400_BAD_REQUEST)

        order.rating = rating
        order.save()
        return Response({"detail": "Rating submitted"})

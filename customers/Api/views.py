# api/views.py

from rest_framework import status,generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password
from .serializers import MakerRegisterSerializer, CheckerRegisterSerializer, UserLoginSerializer,CheckerRequestSerializer
from .serializers import CustomerDataSerializer,CustomTokenObtainPairSerializer,MakerRequestSerializer, CustomerDataUploadSerializer
from customer_management.settings import db
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from bson import ObjectId
from customers.models import MongoUser
from rest_framework.permissions import IsAuthenticated
from bson.objectid import ObjectId
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class RegisterMakerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = MakerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            username = user_data.get('username')
            password = make_password(user_data.get('password'))
            checker_username = user_data.get('checker_username')

            if db.users.find_one({"username": username}):
                return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

            checker = db.users.find_one({"username": checker_username, "is_checker": True})
            if not checker:
                return Response({'error': 'Checker not found'}, status=status.HTTP_400_BAD_REQUEST)

            user = {
                "username": username,
                "password": password,
                "is_maker": True,
                "is_checker": False,
                "checkers": [checker_username]
            }

            db.users.insert_one(user)
            return Response({'message': 'Maker registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterCheckerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = CheckerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data
            username = user_data.get('username')
            password = make_password(user_data.get('password'))

            if db.users.find_one({"username": username}):
                return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

            user = {
                "username": username,
                "password": password,
                "is_maker": False,
                "is_checker": True,
                "checkers": []  # Checkers do not have checkers
            }

            db.users.insert_one(user)
            return Response({'message': 'Checker registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password')

            user_data = db.users.find_one({"username": username})
            if user_data and check_password(password, user_data['password']):
                user = MongoUser(user_data)
                refresh = RefreshToken.for_user(user)

                # Add username to the token
                refresh['username'] = username

                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class MakersUnderCheckerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = CheckerRequestSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            
            # Check if the user is a checker
            checker_data = db.users.find_one({"username": username, "is_checker": True})
            if checker_data:
                # Find all makers under this checker
                makers = db.users.find({"is_maker": True, "checkers": username})
                makers_list = [{"username": maker["username"], "id": str(maker["_id"])} for maker in makers]
                return Response({"makers": makers_list}, status=status.HTTP_200_OK)
            return Response({"error": "Checker not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user_data = db.users.find_one({"username": username})
        if user_data and check_password(password, user_data['password']):
            user = MongoUser(user_data)
            refresh = self.get_serializer_class().get_token(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
    

class UploadCustomerDataView(generics.GenericAPIView):
    serializer_class = CustomerDataUploadSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            photo = request.FILES['photo']
            resume = request.FILES['resume']

            photo_path = default_storage.save(f'photos/{photo.name}', ContentFile(photo.read()))
            resume_path = default_storage.save(f'resumes/{resume.name}', ContentFile(resume.read()))

            email = db.customerdata.find_one({"email": serializer.validated_data['email']})
            if email:
                return Response({"error": "Customer already registered with this email"}, status=status.HTTP_400_BAD_REQUEST)

            data = {
                "maker_username": serializer.validated_data['maker_username'],
                "photo": photo_path,
                "resume": resume_path,
                "customer_name": serializer.validated_data['customer_name'],
                "email": serializer.validated_data['email'],
                "status": "Pending",
            }
            result = db.customerdata.insert_one(data)
            return Response({"id": str(result.inserted_id)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerDataView(APIView):
    def post(self, request, format=None):
        serializer = MakerRequestSerializer(data=request.data)
        if serializer.is_valid():
            maker_username = serializer.validated_data.get('maker_username')

            # Retrieve customer data based on maker_username
            customer_data_cursor = db.customerdata.find({"maker_username": maker_username})
            print('ddd',customer_data_cursor)
            customer_data_list = list(customer_data_cursor)

            if not customer_data_list:
                return Response({"error": "No customer data found for the given maker username"}, status=status.HTTP_404_NOT_FOUND)
            
            serialized_data = []
            for data in customer_data_list:
                data['customer_name']=data['customer_name']
                data['status'] = data['status']
                data['email']=data['email']
                
                
                customer_serializer = CustomerDataSerializer(data=data)
                if customer_serializer.is_valid():
                    serialized_data.append(customer_serializer.data)
                else:
                    return Response(customer_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(serialized_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





class MakersUnderCheckerView(APIView):
    def post(self, request, format=None):
        checker_username = request.data.get('checker_username')

        # Query MongoDB to find all makers under the checker
        makers = db.users.find({"is_maker": True, "checkers": checker_username})

        response_data = []
        for maker in makers:
            # Retrieve customer data associated with this maker
            customer_data = db.customerdata.find({"maker_username": maker['username']})

            # Construct response for each maker
            maker_info = {
                'id': str(maker['_id']),
                'username': maker['username'],
                'customers': []
            }

            for customer in customer_data:
                maker_info['customers'].append({
                    'id': str(customer['_id']),
                    'customer_name': customer['customer_name'],
                    'status': customer['status'],
                
                })

            response_data.append(maker_info)

        return Response({'makers': response_data}, status=status.HTTP_200_OK)
    
    

        
class StatusUpdateApprove(APIView):
    def post(self, request, format=None):
        checker_username = request.data.get('checker_username')
        customer_id = request.data.get('customer_id')
        status_value = 'Approve'

        makers = db.users.find({"checker_username": checker_username})

        if not makers:
                return Response({"error": "No makers found under the checker"}, status=status.HTTP_404_NOT_FOUND)
            
        customer = db.customerdata.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        

        try:
            
            db.customerdata.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": {"status": status_value}}
            )
            return Response('Data updated successfully', status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class StatusUpdateDecline(APIView):
    def post(self, request, format=None):
        checker_username = request.data.get('checker_username')
        customer_id = request.data.get('customer_id')
        status_value = 'Decline'

        makers = db.users.find({"checker_username": checker_username})

        if not makers:
                return Response({"error": "No makers found under the checker"}, status=status.HTTP_404_NOT_FOUND)
            
        customer = db.customerdata.find_one({"_id": ObjectId(customer_id)})
        if not customer:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        

        try:
            
            db.customerdata.update_one(
                {"_id": ObjectId(customer_id)},
                {"$set": {"status": status_value}}
            )
            return Response('Data updated successfully', status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
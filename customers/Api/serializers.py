from rest_framework import serializers

# api/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from bson import ObjectId

class MakerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    checker_username = serializers.CharField(required=True)

class CheckerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    
    

class CheckerRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    
    


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_id'] = str(user.id) 
        token['username'] = user.username
        return token
    
    

class CustomerDataSerializer(serializers.Serializer):
    customer_name=serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    


class CustomerDataUploadSerializer(serializers.Serializer):
    maker_username = serializers.CharField(max_length=255)
    photo = serializers.ImageField()
    resume = serializers.FileField()
    email = serializers.EmailField()
    customer_name=serializers.CharField(max_length=255)



class StatusUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=255)
    
class MakerRequestSerializer(serializers.Serializer):
    maker_username = serializers.CharField(max_length=255)
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from users.models import User, DoctorPersonalDetail, Patient, Receptionist


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')

        if phone and password:
            user = authenticate(request=self.context.get('request'), phone=phone, password=password)
            if user is None:
                raise serializers.ValidationError('Invalid phone number or password.')
            if not user.is_active:
                raise serializers.ValidationError('This account is inactive.')
        else:
            raise serializers.ValidationError('Must include "phone" and "password".')

        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone',"is_doctor",'is_receptionist', 'date_created', 'date_updated']


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorPersonalDetail
        fields = [
            'id', 'user_created', 'email', 'profile_img', 'highest_qualification',
            'hospital_address', 'medical_registration_number', 'graduation_year',
            'specialty', 'date_created', 'date_updated', 'first_name', 'last_name',
            'phone_number', 'status', 'is_verified_doctor', 'user'
        ]

class PatientSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    middle_name = serializers.SerializerMethodField()
    class Meta:
        model = Patient
        fields = '__all__'
    
    def get_first_name(self, obj):
        if obj.first_name is not None:
            return obj.first_name.title()
        return None

    def get_last_name(self, obj):
        if obj.last_name is not None:
            return obj.last_name.title()
        return None
    
    def get_middle_name(self, obj):
        if obj.middle_name is not None:
            return obj.middle_name.title()
        return None

class ReceptionistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receptionist
        fields = '__all__'
from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from users.models import User
from users.filters import UserFilter
from users.serializers import (
    LoginSerializer,
    UserSerializer
)
from .models import DoctorPersonalDetail, Patient, Receptionist
from .serializers import DoctorSerializer, PatientSerializer, ReceptionistSerializer
from users.filters import DoctorPersonalDetailFilter, PatientFilter, ReceptionistFilter
from django.core.paginator import Paginator


class RegisterView(APIView):
    def post(self, request):
        # Extracting each field manually from the request data
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        phone = request.data.get('phone')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        # Validation for mandatory fields
        if not first_name or not last_name or not email or not phone or not password:
            return Response({'error': 'Please provide all required fields.'},  status=status.HTTP_400_BAD_REQUEST)

        # Checking if passwords match
        if password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Checking if email or phone already exists
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Phone number already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        # Creating user object and saving manually
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone
        )

        # Hashing password and saving user
        user.set_password(password)
        user.save()

        # Handle doctor details if provided
        doctor_data = request.data.get("doctor_personal_detail")
        if doctor_data:
            # Exclude common fields and set the user instance
            doctor_data['first_name'] = first_name
            doctor_data['last_name'] = last_name
            doctor_data['email'] = email
            doctor_data['phone'] = phone
            doctor_data['user'] = user.id
            user_api = UserAPI()
            user_api.data = doctor_data
            user_api.user = user  # Pass user reference
            user_api.postDoctorPersonalDetail()  # Call method for doctor detail creation

            # Handle errors during doctor detail creation
            if user_api.status != status.HTTP_201_CREATED:
                user.delete()  # Roll back user creation if doctor creation fails
                return Response(user_api.ctx, status=user_api.status)

        # Generating JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Serializing the user data for response
        user_data = UserSerializer(user).data

        # Adding tokens to the response
        user_data['access'] = access_token
        user_data['refresh'] = refresh_token
        return Response(user_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            tokens = serializer.save()
            return Response(tokens, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAPI(APIView):
    """MedicineData view"""
    # permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        self.data = request.GET
        self.pk = None
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "getUser": self.getUser,
                "getDoctorPersonalDetail": self.getDoctorPersonalDetail,
                "getPatient": self.getPatient,
                "getReceptionist": self.getReceptionist,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status(request)
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def getUser(self, request):
        filterset_class = UserFilter
        try:
            # get the page details
            page_number = int(self.data.get("page", 1))
            records_number = int(self.data.get("records_number", 10))

            data = User.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            # calculating total records
            total_count = filtered_queryset.count()
            # Applying pagination
            paginator = Paginator(filtered_queryset, records_number)
            page_data = paginator.page(page_number)
            serializer = UserSerializer(page_data, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "successfully getting User!", "data": serializer, "total_count": total_count} # noqa
            self.status = status.HTTP_200_OK
        except Exception:
            self.ctx = {"message": "not getting data!"}
            self.status = status.HTTP_404_NOT_FOUND

    def getDoctorPersonalDetail(self, request):
        filterset_class = DoctorPersonalDetailFilter
        try:
            data = DoctorPersonalDetail.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            serializer = DoctorSerializer(filtered_queryset, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "Successfully retrieved doctor data!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": f"Error: {str(e)}"}
            self.status = status.HTTP_404_NOT_FOUND

    def getPatient(self, request):
        filterset_class = PatientFilter
        try:
            data = Patient.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            serializer = PatientSerializer(filtered_queryset, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "Successfully retrieved Patient data!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": f"Error: {str(e)}"}
            self.status = status.HTTP_404_NOT_FOUND

    def getReceptionist(self, request):
        filterset_class = ReceptionistFilter
        try:
            data = Receptionist.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            serializer = ReceptionistSerializer(filtered_queryset, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "Successfully retrieved Patient data!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": f"Error: {str(e)}"}
            self.status = status.HTTP_404_NOT_FOUND

    def post(self, request):
        self.data = request.data
        self.pk = None
        self.user = request.user
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "postUser": self.postUser,
                "postDoctorPersonalDetail": self.postDoctorPersonalDetail,
                "postPatient": self.postPatient,
                "postReceptionist": self.postReceptionist,
                # Add more actions as needed
            }

            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def postUser(self):
        first_name = self.data.get("first_name")
        last_name = self.data.get("last_name")
        email = self.data.get("email")
        phone = self.data.get("phone")
        is_doctor = self.data.get("is_doctor")
        is_receptionist = self.data.get("is_receptionist")

        try:
            obj = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                is_doctor = is_doctor if is_doctor else False,
                is_receptionist = is_receptionist if is_receptionist else False,
            )
            obj.save()
            serializer = UserSerializer(obj).data
            self.ctx = {"message": "User is Created!", "data": serializer} # noqa
            self.status = status.HTTP_201_CREATED
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def postDoctorPersonalDetail(self):
        first_name = self.data.get("first_name")
        last_name = self.data.get("last_name")
        email = self.data.get("email")
        phone = self.data.get("phone")
        profile_img = self.data.get("profile_img")
        highest_qualification = self.data.get("highest_qualification")
        hospital_address = self.data.get("hospital_address")
        medical_registration_number = self.data.get("medical_registration_number")
        graduation_year = self.data.get("graduation_year")
        specialty = self.data.get("specialty")
        doctor_status = self.data.get("status")
        is_verified_doctor = self.data.get("is_verified_doctor")
        user = self.data.get("user")
        user_created = self.user

        try:
            user = User.objects.get(pk=user)
            obj = DoctorPersonalDetail(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone,
                profile_img=profile_img,
                highest_qualification=highest_qualification,
                hospital_address=hospital_address,
                medical_registration_number=medical_registration_number,
                graduation_year=graduation_year,
                specialty=specialty,
                status=doctor_status,
                is_verified_doctor=is_verified_doctor,
                user=user,
                user_created=user_created
            )

            obj.save()
            serializer = DoctorSerializer(obj).data
            self.ctx = {"message": "User is Created!", "data": serializer} # noqa
            self.status = status.HTTP_201_CREATED
        except User.DoesNotExist:
            self.ctx = {"message": "User not found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def postPatient(self):
        first_name = self.data.get("first_name")
        middle_name = self.data.get("middle_name")
        last_name = self.data.get("last_name")
        phone = self.data.get("phone")
        address = self.data.get("address")
        user_created = self.user
        print("")
        try:

            obj = Patient(
                first_name = first_name,
                middle_name = middle_name,
                last_name = last_name,
                phone=phone,
                address = address,
                user_created=user_created
            )

            obj.save()
            serializer = PatientSerializer(obj).data
            self.ctx = {"message": "Patient is Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED

        except User.DoesNotExist:
            self.ctx = {"message": "User not found!"}
            self.status = status.HTTP_404_NOT_FOUND

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def postReceptionist(self):
        first_name = self.data.get("first_name")
        middle_name = self.data.get("middle_name")
        last_name = self.data.get("last_name")
        phone = self.data.get("phone")
        email = self.data.get("email")
        user_created = self.user
        print("")
        try:

            obj = Receptionist(
                first_name = first_name,
                middle_name = middle_name,
                last_name = last_name,
                phone=phone,
                email = email,
                user_created=user_created
            )

            obj.save()
            serializer = PatientSerializer(obj).data
            self.ctx = {"message": "Receptionist is Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED

        except User.DoesNotExist:
            self.ctx = {"message": "User not found!"}
            self.status = status.HTTP_404_NOT_FOUND

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def patch(self, request):
        self.data = request.data
        self.pk = None
        self.user = request.user
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if "id" in self.data:
            self.id = self.data["id"]

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "patchUser": self.patchUser,
                "patchDoctorPersonalDetail": self.patchDoctorPersonalDetail,
                "patchPatient": self.patchPatient,
                "patchReceptionist": self.patchReceptionist,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def patchUser(self):
        first_name = self.data.get("first_name")
        last_name = self.data.get("last_name")
        email = self.data.get("email")
        phone = self.data.get("phone")

        try:
            users = User.objects.filter(pk=self.id)
            if users.exists():
                users = users[0]
            else:
                self.ctx = {"message": f"users id {self.id} Not Found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            if first_name:
                users.first_name = first_name
            if last_name:
                users.last_name = last_name
            if phone:
                users.phone = phone
            if email:
                users.email = email
            users.save()
            serializer = UserSerializer(users).data
            self.ctx = {"message": "users is Updated!", "data": serializer}
            self.status = status.HTTP_201_CREATED
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def patchDoctorPersonalDetail(self):
        first_name = self.data.get("first_name")
        last_name = self.data.get("last_name")
        email = self.data.get("email")
        phone_number = self.data.get("phone_number")
        profile_img = self.data.get("profile_img")
        highest_qualification = self.data.get("highest_qualification")
        hospital_address = self.data.get("hospital_address")
        medical_registration_number = self.data.get("medical_registration_number")
        graduation_year = self.data.get("graduation_year")
        specialty = self.data.get("specialty")
        doctor_status = self.data.get("status")
        is_verified_doctor = self.data.get("is_verified_doctor")
        user = self.data.get("user")
        print(self.id)
        try:
            doctors = DoctorPersonalDetail.objects.filter(pk=self.id)
            if doctors.exists():
                doctor = doctors.first()
            else:
                self.ctx = {"message": f"Doctor id {self.id} Not Found!"}
                self.status = doctor_status.HTTP_404_NOT_FOUND
                return
            if first_name:
                doctor.first_name = first_name
            if last_name:
                doctor.last_name = last_name
            if email:
                doctor.email = email
            if phone_number:
                doctor.phone_number = phone_number
            if profile_img:
                doctor.profile_img = profile_img
            if highest_qualification:
                doctor.highest_qualification = highest_qualification
            if hospital_address:
                doctor.hospital_address = hospital_address
            if medical_registration_number:
                doctor.medical_registration_number = medical_registration_number
            if graduation_year:
                doctor.graduation_year = graduation_year
            if specialty:
                doctor.specialty = specialty
            if doctor_status:
                doctor.status = doctor_status
            if is_verified_doctor is not None:
                doctor.is_verified_doctor = is_verified_doctor
            if user:
                user = User.objects.get(pk=user)
                doctor.user = user
            doctor.save()
            serializer = DoctorSerializer(doctor).data
            self.ctx = {"message": "Doctor is Updated!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def patchPatient(self):
        first_name = self.data.get("first_name")
        middle_name = self.data.get("middle_name")
        last_name = self.data.get("last_name")
        phone = self.data.get("phone")
        address = self.data.get("address")

        try:
            patients = Patient.objects.filter(pk=self.id)
            if patients.exists():
                patient = patients.first()
            else:
                self.ctx = {"message": f"Patient id {self.id} Not Found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return

            if first_name:
                patient.first_name = first_name
            if middle_name:
                patient.middle_name = middle_name
            if last_name:
                patient.last_name = last_name
            if phone:
                patient.phone = phone
            if address:
                patient.address = address
            patient.save()
            serializer = PatientSerializer(patient).data
            self.ctx = {"message": "Patient is Updated!", "data": serializer}
            self.status = status.HTTP_200_OK

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def patchReceptionist(self):
        first_name = self.data.get("first_name")
        middle_name = self.data.get("middle_name")
        last_name = self.data.get("last_name")
        phone = self.data.get("phone")
        email = self.data.get("email")

        try:
            receptionist = Receptionist.objects.filter(pk=self.id)
            if receptionist.exists():
                receptionist = receptionist.first()
            else:
                self.ctx = {"message": f"Receptionist id {self.id} Not Found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return

            if first_name:
                receptionist.first_name = first_name
            if middle_name:
                receptionist.middle_name = middle_name
            if last_name:
                receptionist.last_name = last_name
            if phone:
                receptionist.phone = phone
            if email:
                receptionist.email = email
            receptionist.save()
            serializer = ReceptionistSerializer(receptionist).data
            self.ctx = {"message": "Receptionist is Updated!", "data": serializer}
            self.status = status.HTTP_200_OK

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def delete(self, request):
        self.data = request.data
        self.pk = None
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if "id" in self.data:
            self.id = self.data["id"]

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "delUser": self.delUser,
                "delDoctorPersonalDetail": self.delDoctorPersonalDetail,
                "delPatient": self.delPatient,
                "getReceptionist": self.getReceptionist,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def delUser(self):
        try:
            data = User.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "User deleted!"}
            self.status = status.HTTP_201_CREATED
        except User.DoesNotExist:
            self.ctx = {"message": "User id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def delDoctorPersonalDetail(self):
        try:
            data = DoctorPersonalDetail.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Doctor deleted!"}
            self.status = status.HTTP_200_OK
        except DoctorPersonalDetail.DoesNotExist:
            self.ctx = {"message": "Doctor id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def delPatient(self):
        try:
            data = Patient.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Patient deleted!"}
            self.status = status.HTTP_200_OK
        except Patient.DoesNotExist:
            self.ctx = {"message": "Patient id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def delReceptionist(self):
        try:
            data = Receptionist.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Receptionist deleted!"}
            self.status = status.HTTP_200_OK
        except Receptionist.DoesNotExist:
            self.ctx = {"message": "Receptionist id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

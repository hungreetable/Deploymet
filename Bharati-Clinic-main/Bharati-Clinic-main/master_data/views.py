from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rapidfuzz import process, fuzz
from django.core.paginator import Paginator
from .models import MedicineData, GenericName, MedicineType
from .serializers import MedicineDataSerializer, GenericNameSerializer, MedicineTypeSerializer
from .filters import MedicineDataFilter, GenericNameFilter, MedicineTypeFilter

class SpellCheckMedicine(APIView):
    def post(self, request):
        extracted_medicines = request.data  # Get JSON object
        
        if not isinstance(extracted_medicines, dict):
            return Response({"error": "Invalid input format. Expected JSON object."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fetch all medicine names from the database
        medicine_list = list(MedicineData.objects.values_list("name", flat=True))

        # Function to correct names
        def correct_medicines(extracted_medicines, medicine_list, threshold=50):
            corrected_medicines = {}

            for key, medicine in extracted_medicines.items():
                best_match, score, _ = process.extractOne(medicine, medicine_list, scorer=fuzz.ratio)

                if score >= threshold:
                    corrected_medicines[key] = best_match  # Replace incorrect name
                else:
                    corrected_medicines[key] = None  # No close match found

            return corrected_medicines

        # Run correction
        corrected = correct_medicines(extracted_medicines, medicine_list)

        return Response(corrected, status=status.HTTP_200_OK)
    
class MedicineAPI(APIView):
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
                "getMedicineData":self.getMedicineData,
                "getMedicineType":self.getMedicineType,
                "getGenericName":self.getGenericName,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status(request)
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
        
    def getMedicineData(self, request):
        filterset_class = MedicineDataFilter
        try:
            page_number = int(self.data.get("page", 1))
            records_number = int(self.data.get("records_number", 10))

            data = MedicineData.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            total_count = filtered_queryset.count()

            paginator = Paginator(filtered_queryset, records_number)
            page_data = paginator.page(page_number)

            serializer = MedicineDataSerializer(page_data, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]

            self.ctx = {"message": "Successfully retrieved medicine data!", "data": serializer, "total_count": total_count}
            self.status = status.HTTP_200_OK

        except Exception:
            self.ctx = {"message": "Error retrieving medicine data!"}
            self.status = status.HTTP_404_NOT_FOUND

    def getGenericName(self, request):
        filterset_class = GenericNameFilter
        try:
            page_number = int(self.data.get("page", 1))
            records_number = int(self.data.get("records_number", 10))

            data = GenericName.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            total_count = filtered_queryset.count()

            paginator = Paginator(filtered_queryset, records_number)
            page_data = paginator.page(page_number)

            serializer = GenericNameSerializer(page_data, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "Successfully retrieved generic name data!", "data": serializer, "total_count": total_count}
            self.status = status.HTTP_200_OK
        except Exception:
            self.ctx = {"message": "Error retrieving generic name data!"}
            self.status = status.HTTP_404_NOT_FOUND

    def getMedicineType(self, request):
        filterset_class = MedicineTypeFilter
        try:

            page_number = int(self.data.get("page", 1))
            records_number = int(self.data.get("records_number", 10))

            data = MedicineType.objects.all()
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            total_count = filtered_queryset.count()

            paginator = Paginator(filtered_queryset, records_number)
            page_data = paginator.page(page_number)

            serializer = MedicineTypeSerializer(page_data, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]
            self.ctx = {"message": "Successfully retrieved medicine type data!", "data": serializer, "total_count": total_count}
            self.status = status.HTTP_200_OK
        except Exception:
            self.ctx = {"message": "Error retrieving medicine type data!"}
            self.status = status.HTTP_404_NOT_FOUND

    def post(self, request):
        self.data = request.data
        self.pk = None
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)
        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "postMedicineData":self.postMedicineData,
                "postMedicineType":self.postMedicineType,
                "postGenericName":self.postGenericName,
            }

            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
    
    def postMedicineData(self):
        name = self.data.get("name")
        price = self.data.get("price")
        quantity = self.data.get("quantity")
        medicine_type = self.data.get("medicine_type")
        generic_name = self.data.get("generic_name")

        try:
            medicine_type = MedicineType.objects.get(pk=medicine_type)
            generic_name = GenericName.objects.get(pk=generic_name)

            if MedicineData.objects.filter(name__iexact=name, medicine_type=medicine_type, generic_name=generic_name).exists():
                self.ctx = {"message": "Medicine with this name already exists!"}
                self.status = status.HTTP_400_BAD_REQUEST
                return
            
            obj = MedicineData(
                name=name,
                price=price,
                quantity=quantity,
                medicine_type=medicine_type,
                generic_name=generic_name
            )
            obj.save()
            serializer = MedicineDataSerializer(obj).data
            self.ctx = {"message": "Medicine Data Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED
                
        except MedicineType.DoesNotExist:
            self.ctx = {"message": "Medicine Type not found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except GenericName.DoesNotExist:
            self.ctx = {"message": "Generic Name not found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def postMedicineType(self):
        name = self.data.get("name")

        try:
            if MedicineType.objects.filter(name__iexact=name).exists():
                self.ctx = {"message": "Medicine Type already exists!"}
                self.status = status.HTTP_400_BAD_REQUEST
                return
            
            obj = MedicineType(name=name)
            obj.save()
            serializer = MedicineTypeSerializer(obj).data
            self.ctx = {"message": "Medicine Type Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def postGenericName(self):
        name = self.data.get("name")

        try:
            if GenericName.objects.filter(name__iexact=name).exists():
                self.ctx = {"message": "Generic Name already exists!"}
                self.status = status.HTTP_400_BAD_REQUEST
                return
            
            obj = GenericName(name=name)
            obj.save()
            serializer = GenericNameSerializer(obj).data
            self.ctx = {"message": "Generic Name Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED
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
                "patchMedicineData":self.patchMedicineData,
                "patchMedicineType":self.patchMedicineType,
                "patchGenericName":self.patchGenericName,

            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def patchMedicineData(self):
        name = self.data.get("name")
        price = self.data.get("price")
        quantity = self.data.get("quantity")
        medicine_type = self.data.get("medicine_type")
        generic_name= self.data.get("generic_name")
        
        try:
            medicine = MedicineData.objects.filter(pk=self.id).first()
            if not medicine:
                self.ctx = {"message": f"MedicineData ID {self.id} not found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            
            if medicine_type:
                medicine.medicine_type = MedicineType.objects.get(pk=medicine_type)
            if generic_name:
                medicine.generic_name = GenericName.objects.get(pk=generic_name)
            if name:
                medicine.name = name
            if price:
                medicine.price = price
            if quantity:
                medicine.quantity = quantity
            
            medicine.save()
            serializer = MedicineDataSerializer(medicine).data
            self.ctx = {"message": "Medicine Data Updated!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def patchMedicineType(self):
        name = self.data.get("name")
        
        try:
            medicine_type = MedicineType.objects.filter(pk=self.id).first()
            if not medicine_type:
                self.ctx = {"message": f"MedicineType ID {self.id} not found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            
            if name:
                medicine_type.name = name
            
            medicine_type.save()
            serializer = MedicineTypeSerializer(medicine_type).data
            self.ctx = {"message": "Medicine Type Updated!", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def patchGenericName(self):
        name = self.data.get("name")
        
        try:
            generic_name = GenericName.objects.filter(pk=self.id).first()
            if not generic_name:
                self.ctx = {"message": f"GenericName ID {self.id} not found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            
            if name:
                generic_name.name = name
            
            generic_name.save()
            serializer = GenericNameSerializer(generic_name).data
            self.ctx = {"message": "Generic Name Updated!", "data": serializer}
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
                "delMedicineData": self.delMedicineData,
                "delMedicineType": self.delMedicineType,
                "delGenericName": self.delGenericName
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option!", "data": None}, status.HTTP_400_BAD_REQUEST)
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST)


    def delMedicineData(self):
        try:
            data = MedicineData.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Medicine Data deleted!"}
            self.status = status.HTTP_200_OK
        except MedicineData.DoesNotExist:
            self.ctx = {"message": "Medicine Data id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def delMedicineType(self):
        try:
            data = MedicineType.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Medicine Type deleted!"}
            self.status = status.HTTP_200_OK
        except MedicineType.DoesNotExist:
            self.ctx = {"message": "Medicine Type id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR


    def delGenericName(self):
        try:
            data = GenericName.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Generic Name deleted!"}
            self.status = status.HTTP_200_OK
        except GenericName.DoesNotExist:
            self.ctx = {"message": "Generic Name id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from image_processing.models import PrescriptionRecord
from image_processing.filters import PrescriptionRecordFilter
from image_processing.serializers import PrescriptionSerializer
import google.generativeai as genai
import PIL.Image
import json
from .models import Patient
from datetime import datetime, timedelta
from django.core.paginator import Paginator


class ImageProcessingAPI(APIView):
    def post(self, request):
        Image = request.FILES.get("image")
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not Image:
            return Response({"error": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            genai.configure(api_key="AIzaSyDV2EqHdJNBJ96S8279tQ1AhDF5roa4axg")
            model = genai.GenerativeModel("gemini-2.0-flash")
            organ = PIL.Image.open(Image)
            response = model.generate_content([
                '''Analyze the provided prescription image and extract the following information into a strict JSON format. Use an empty string "" for any field where information is not present. All text output should be in English.

**Extraction Rules:**

1.  **Patient Details:** Extract Name, Age, Gender.
2.  **Vitals & Info:**
    *   `weight`: Value from the 'Weight' field.
    *   `bp`: Value written below the 'B/P' text.
    *   `place`: Text from the 'Address' field.
    *   `type`: "O" (Old) or "N" (New) based on the character ('O' or 'N') written **below** the 'Type' label.  *(Modification made here)*
    *   `pulse`: Value from the 'Pulse' field.
3.  **Dates:**
    *   `prescription_date`: Extract the date (top right), format as YYYY-MM-DD.
    *   `follow_up_date`: Extract date if mentioned at the very bottom, format as YYYY-MM-DD.
4.  **Clinical Info:**
    *   `complaints`: List any complaints mentioned.
    *   `Lab_test`: List any lab tests requested (format: [{"Test1": "Result"},...]).
5.  **Medications:**
    *   Extract each medication name (exclude prefixes like "Tab.").
    *   Determine dosage timing (morning, afternoon, night) based on the pattern following the name (e.g., '1-0-1', '1 - x - 1', '0 1 1/2').
    *   **Timing Logic:** A digit (like 1, 2, 1/2) means `true` for that time slot (morning, afternoon, night respectively). A symbol (like x, 0, >) or absence means `false`. Handle variations in separators (-, spaces) and potential cursive script.
    *   Format as shown in the JSON structure below.

**Required JSON Output Format:**

{
    "patient_name": "Extracted Name",
    "gender":"F(female) or M(male)",
    "age":"extracted Age",
    "weight":"Extracted Weight",
    "bp":"Extracted B/P",
    "place":"Extracted Address",
    "type":"O(Old) or N(New)",
    "pulse":"Extracted Pulse",
    "Lab_test":[{"Test1":"Result"},...],
    "prescription_date": "YYYY-MM-DD",
    "follow_up_date":"YYYY-MM-DD",
    "complaints":["Fever","cold",...],
    "medications": [
        {
            "name": "Medication Name",
            "timing": {
                "morning": true/false,
                "afternoon": true/false,
                "night": true/false
            }
        },
        ...
    ]
}

                ''', organ]) # noqa

            try:
                json_str = response.text.strip().strip('```json').strip('```').strip()
                json_data = json.loads(json_str)
                return Response(json_data, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": f"Json parsing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Generative ai error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PrescriptionAPI(APIView):
    def get(self, request):
        self.data = request.query_params
        self.pk = None

        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "getPrescriptionRecord": self.getPrescriptionRecord,
                "getPrescriptionCount": self.getPrescriptionCount,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status(request)
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def getPrescriptionRecord(self, request):
        filterset_class = PrescriptionRecordFilter
        from_date = None
        to_date = None
        all_data = self.data.get("all_data", False)
        try:
            page_number = int(request.query_params.get("page", 1))  # Default page is 1
            records_number = int(request.query_params.get("records_number", 10))  # Default records per page is 10

            data = PrescriptionRecord.objects.all().order_by("-date_updated")

            # Filter by 'from_date' and 'to_date' if they exist in query params
            from_date = request.query_params.get("from_date")
            to_date = request.query_params.get("to_date")
            filter_response = request.query_params.get("filter_response")
            type = request.query_params.get("type")

            # Get today's date
            today = datetime.today().date()
            if filter_response == "today":
                from_date = today
                to_date = today  # Only today's records
                data = data.filter(prescription_date__range=[from_date, to_date])

            elif filter_response == "week":
                from_date = today - timedelta(days=today.weekday())  # Start of the current week (Monday)
                to_date = today  # Up to today
                data = data.filter(prescription_date__range=[from_date, to_date])

            elif filter_response == "month":
                from_date = today.replace(day=1)  # First day of the current month
                to_date = today  # Up to today
                data = data.filter(prescription_date__range=[from_date, to_date])

            elif from_date and to_date:
                try:
                    from_date = datetime.strptime(from_date, '%Y-%m-%d')
                    to_date = datetime.strptime(to_date, '%Y-%m-%d')
                    data = data.filter(prescription_date__range=[from_date, to_date])
                except ValueError:
                    return Response({"message": "Invalid date format. Use YYYY-MM-DD."},
                                    status=status.HTTP_400_BAD_REQUEST)

            elif from_date:
                try:
                    from_date = datetime.strptime(from_date, '%Y-%m-%d')
                    # Filter records for the specific date
                    data = data.filter(
                        prescription_date__gte=from_date,
                        prescription_date__lt=from_date
                    )
                except ValueError:
                    return Response({"message": "Invalid single_date format. Use YYYY-MM-DD."},
                                    status=status.HTTP_400_BAD_REQUEST)
            
            if type in ["O", "N", "L"]:
                data = data.filter(type=type)

            filtered_queryset = filterset_class(request.query_params, queryset=data).qs

            # calculating total records
            total_count = filtered_queryset.count()

            if all_data:
                serializer = PrescriptionSerializer(filtered_queryset, many=True).data
                self.ctx = {"message": "Successfully getting Prescription Record!", "data": serializer, "total_count": total_count}
                self.status = status.HTTP_200_OK
                return

            # Applying pagination
            paginator = Paginator(filtered_queryset, records_number)
            page_data = paginator.page(page_number)

            serializer = PrescriptionSerializer(page_data, many=True).data
            if self.pk and len(serializer):
                serializer = serializer[0]

            self.ctx = {"message": "Successfully getting Prescription Record!", "data": serializer, "total_count": total_count}
            self.status = status.HTTP_200_OK

        except Exception:
            self.ctx = {"message": "Error in fetching data!"}
            self.status = status.HTTP_404_NOT_FOUND
    

    def getPrescriptionCount(self, request):
        """ Get total prescription count with gender-wise breakdown. """
        try:
            # Get today's date as default
            filterset_class = PrescriptionRecordFilter
            from_date = request.query_params.get("from_date")
            to_date = request.query_params.get("to_date")
            today = datetime.today().date()

            if not from_date:
                from_date = today.strftime("%Y-%m-%d")
            if not to_date:
                to_date = today.strftime("%Y-%m-%d")


            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d").date()  # Convert to date
                to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            except ValueError:
                return Response({"message": "Invalid date format. Use YYYY-MM-DD."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Get all prescription records within the date range
            data = PrescriptionRecord.objects.filter(prescription_date__range=[from_date, to_date])

            # Apply filters from filter.py
            filtered_queryset = filterset_class(request.query_params, queryset=data).qs
            # Calculate counts
            total_count = filtered_queryset.count()
            male_count = filtered_queryset.filter(gender="M").count()
            female_count = filtered_queryset.filter(gender="F").count()
            old_count = filtered_queryset.filter(type="O").count()
            new_count = filtered_queryset.filter(type="N").count()
            late_count = filtered_queryset.filter(type="L").count()

            # Prepare response
            self.ctx = {
                "message": "Successfully retrieved prescription count!",
                "total_count": total_count,
                "Male": male_count,
                "Female": female_count,
                "Old": old_count,
                "New": new_count,
                "Late": late_count,
            }
            self.status = status.HTTP_200_OK

        except Exception:
            self.ctx = {"message": "Error in fetching data!"}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def post(self, request):
        self.data = request.data
        self.user = request.user
        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "postPrescriptionRecord": self.postPrescriptionRecord,
                # "downloadExcel": self.downloadExcel,
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

    def postPrescriptionRecord(self):
        patient = self.data.get("patient")
        patient_name = self.data.get('patient_name').lower()
        prescription_date = self.data.get('prescription_date')
        medications = self.data.get('medications')
        complaints = self.data.get('complaints', [])
        gender = self.data.get('gender', "")
        age = self.data.get('age', "")
        weight = self.data.get('weight', "")
        bp = self.data.get('bp', "")
        place = self.data.get('place', "")
        follow_up_date = self.data.get('follow_up_date')
        pulse = self.data.get('pulse', "")
        lab_test = self.data.get('lab_test', [])
        Type = self.data.get('type')  # Expecting "O" or "N" from user
        phone = self.data.get('phone')
        user_created = self.user
        try:
            def create_new_patient_from_name(name):
                name_parts = name.split()
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                middle_name = name_parts[1] if len(name_parts) > 2 else ""
                last_name = name_parts[-1] if len(name_parts) > 1 else ""
                
                return Patient.objects.create(
                    first_name=first_name,
                    middle_name=middle_name,
                    last_name=last_name,
                    phone=phone,
                    address=place,
                    user_created=user_created
                )
            
            name_parts = patient_name.split()
            first_name = name_parts[0] if len(name_parts) > 0 else None
            last_name=name_parts[-1] if len(name_parts) > 1 else None
            middle_name=name_parts[1] if len(name_parts) > 2 else None

            base_qs = Patient.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            )
            if middle_name:
                # Check for exact match with middle name
                existing_patient = base_qs.filter(middle_name__iexact=middle_name).first()
            else:
                # If no middle name is given, block creation if *any* patient exists with same first+last
                existing_patient = base_qs.exclude(middle_name=None).first()

            if Type == "N":
                if existing_patient:
                    self.ctx = {"message": "Given Patient name is already exist."}
                    self.status = status.HTTP_400_BAD_REQUEST
                    return

                elif not patient_name:
                    self.ctx = {"message": "Patient name is required for new patients."}
                    self.status = status.HTTP_400_BAD_REQUEST
                    return
                patient_obj = create_new_patient_from_name(patient_name)


            elif Type == "O":
                if patient:
                    try:
                        patient_obj = Patient.objects.get(id=patient)
                    except Patient.DoesNotExist:
                        if not patient_name:
                            self.ctx = {"message": "Patient name required if patient not found."}
                            self.status = status.HTTP_400_BAD_REQUEST
                            return
                        patient_obj = create_new_patient_from_name(patient_name)
                else:
                    if not patient_name:
                        self.ctx = {"message": "Patient name is required for fallback creation."}
                        self.status = status.HTTP_400_BAD_REQUEST
                        return
                    elif existing_patient:
                        self.ctx = {"message": "Given Patient name is already exist."}
                        self.status = status.HTTP_400_BAD_REQUEST
                        return
                    patient_obj = create_new_patient_from_name(patient_name)

            else:
                self.ctx = {"message": "Invalid type. Must be 'O' or 'N'."}
                self.status = status.HTTP_400_BAD_REQUEST
                return

            obj = PrescriptionRecord(
                patient=patient_obj,
                patient_name=patient_name,
                prescription_date=prescription_date,
                medications=medications,
                complaints=complaints,
                gender=gender,
                age=age,
                weight=weight,
                bp=bp,
                place=place,
                follow_up_date=follow_up_date,
                pulse=pulse,
                lab_test=lab_test,
                type=Type
            )
            obj.save()
            serializer = PrescriptionSerializer(obj).data
            self.ctx = {"message": "Prescription data is Created!", "data": serializer}
            self.status = status.HTTP_201_CREATED

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

        # if not patient:
        #     self.ctx = {"message": "Patient ID is required."}
        #     self.status = status.HTTP_400_BAD_REQUEST
        #     return
        # try:
        #     patient = Patient.objects.get(id=patient)
        # except Patient.DoesNotExist:
        #     self.ctx = {"message": "Patient not found."}
        #     self.status = status.HTTP_404_NOT_FOUND
        #     return
        
        # try:
        #     obj = PrescriptionRecord(
        #         patient=patient,
        #         patient_name=patient_name,
        #         prescription_date=prescription_date,
        #         medications=medications,
        #         complaints=complaints,
        #         gender=gender,
        #         age=age,
        #         weight=weight,
        #         bp=bp,
        #         place=place,
        #         follow_up_date=follow_up_date,
        #         pulse=pulse,
        #         lab_test=lab_test,
        #         type=type
        #     )
        #     obj.save()
        #     serializer = PrescriptionSerializer(obj).data
        #     self.ctx = {"message": "Prescription data is Created!", "data": serializer}
        #     self.status = status.HTTP_201_CREATED

        # except Exception as e:
        #     self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
        #     self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def patch(self, request):
        self.data = request.data

        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if "id" in self.data:
            self.id = self.data["id"]

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "patchPrescriptionRecord": self.patchPrescriptionRecord
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

    def patchPrescriptionRecord(self):
        patient = self.data.get("patient")
        patient_name = self.data.get('patient_name')
        prescription_date = self.data.get('prescription_date')
        medications = self.data.get('medications')
        complaints = self.data.get('complaints')
        gender = self.data.get('gender')
        age = self.data.get('age')
        weight = self.data.get('weight')
        bp = self.data.get('bp')
        place = self.data.get('place')
        follow_up_date = self.data.get('follow_up_date')
        pulse = self.data.get('pulse')
        lab_test = self.data.get('lab_test')
        type = self.data.get('type')

        try:
            prescriptions = PrescriptionRecord.objects.filter(pk=self.id)
            if prescriptions.exists():
                prescriptions = prescriptions[0]
            else:
                self.ctx = {"message": f"users id {self.id} Not Found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            if patient:
                try:
                    Patient.objects.get(id=patient)
                except Patient.DoesNotExist:
                    self.ctx = {"message": "Patient not found."}
                    self.status = status.HTTP_404_NOT_FOUND
                    return
                prescriptions.patient = patient
            if patient_name:
                prescriptions.patient_name = patient_name
            if prescription_date:
                prescriptions.prescription_date = prescription_date
            if medications:
                prescriptions.medications = medications
            if complaints:
                prescriptions.complaints = complaints
            if gender:
                prescriptions.gender = gender
            if age:
                prescriptions.age = age
            if weight:
                prescriptions.weight = weight
            if bp:
                prescriptions.bp = bp
            if place:
                prescriptions.place = place
            if follow_up_date:
                prescriptions.follow_up_date = follow_up_date
            if pulse:
                prescriptions.pulse = pulse
            if lab_test:
                prescriptions.lab_test = lab_test  # Replace existing lab_test data
            if type:
                prescriptions.type = type

            prescriptions.save()
            serializer = PrescriptionSerializer(prescriptions).data
            self.ctx = {"message": "users is Updated!", "data": serializer}
            self.status = status.HTTP_201_CREATED

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def delete(self, request):
        self.data = request.data

        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if "id" in self.data:
            self.id = self.data["id"]

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "delPrescriptionRecord": self.delPrescriptionRecord
            }

            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa

    def delPrescriptionRecord(self):
        try:
            data = PrescriptionRecord.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Prescription Record deleted!"}
            self.status = status.HTTP_201_CREATED
        except PrescriptionRecord.DoesNotExist:
            self.ctx = {"message": "Prescription Record id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

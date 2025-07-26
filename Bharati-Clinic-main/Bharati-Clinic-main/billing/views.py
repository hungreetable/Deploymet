from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from django.core.paginator import Paginator
from .models import PatientCharge, Patient, PrescriptionRecord, ClinicCharge
from django.db.models import F, ExpressionWrapper, IntegerField, Case, When, Value, Sum, FloatField
from .serializers import PatientChargeSerializer, ClinicChargeSerializer
from .filters import PatientChargeFilter
from datetime import datetime, timedelta

# Create your views here.

class BillingAPI(APIView):
    def get(self, request):
            self.data = request.query_params
            self.pk = None
            self.ctx = {}
            self.status = status.HTTP_400_BAD_REQUEST

            if not request.user.is_authenticated:
                return Response({"message": "Authentication credentials were not provided."},
                                status=status.HTTP_401_UNAUTHORIZED)

            if "id" in self.data:
                self.pk = self.data.get("id")

            if "action" in self.data:
                action = str(self.data["action"])
                action_mapper = {
                    "getBilling": self.getBilling,
                    "getTestFee":self.getTestFee,
                }
                action_status = action_mapper.get(action)
                print(action_status)
                if action_status:
                    action_status(request)
                else:
                    return Response({"message": "Choose Wrong Option!", "data": None}, status.HTTP_400_BAD_REQUEST)
                return Response(self.ctx, self.status)
            else:
                return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST)
            
    def getTestFee(self, request):
        try:
            clinic_charge = ClinicCharge.objects.last()
            if not clinic_charge:
                self.ctx = {"message": "No Clinic Charges Found"}
                self.status = status.HTTP_404_NOT_FOUND
                return
            serializer = ClinicChargeSerializer(clinic_charge).data
            self.ctx = {"message": "Clinic Charges fetched successfully", "data": serializer}
            self.status = status.HTTP_200_OK
        except Exception as e:
            self.ctx = {"message": "Failed to fetch Clinic Charges", "error": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def getBilling(self, request):
            filterset_class = PatientChargeFilter
            all_data = self.data.get("all_data", False)

            try:
                page_number = int(request.query_params.get("page", 1))
                records_number = int(request.query_params.get("records_number", 10))

                # data = PatientCharge.objects.all().order_by("-date_updated")
                data = PatientCharge.objects.select_related("patient", "prescriptionRecord").order_by("-date_updated")

                # Apply filters
                filtered_queryset = filterset_class(request.query_params, queryset=data).qs

                # Apply total_cost annotation here
                charges = ClinicCharge.objects.last()
                if charges:
                    filtered_queryset = filtered_queryset.annotate(
                        total_cost=ExpressionWrapper(
                            F('first_check_up') +
                            F('follow_up_check_up') +
                            F('one_month_late_check_up') +
                            F('stress_test') +
                            F('ecg_test') +
                            F('morning_ect_injection') +
                            F('injection_in_back') +
                            F('counselling_session') +
                            F('evening_first_check_up') +
                            F('evening_follow_up_check_up') +
                            F('special_appointment_check_up'),
                            output_field=FloatField()
                        )
    )
                total_count = filtered_queryset.count()

                # Calculate grand total cost
                grand_total_cost = filtered_queryset.aggregate(total=Sum("total_cost"))["total"] or 0

                if all_data:
                    serializer = PatientChargeSerializer(filtered_queryset, many=True).data
                    self.ctx = {"message": "Successfully fetched Patient Charges!", "data": serializer, "grand_total_cost": grand_total_cost,  "total_count": total_count}
                    self.status = status.HTTP_200_OK
                    return

                # Apply pagination
                paginator = Paginator(filtered_queryset, records_number)
                page_data = paginator.page(page_number)

                serializer = PatientChargeSerializer(page_data, many=True).data
                if self.pk and len(serializer):
                    serializer = serializer[0]

                self.ctx = {
                    "message": "Successfully fetched Patient Charges!",
                    "data": serializer,
                    "total_count": total_count,
                    "grand_total_cost": grand_total_cost
                }
                self.status = status.HTTP_200_OK

            except Exception:
                self.ctx = {"message": "Error in fetching data!"}
                self.status = status.HTTP_404_NOT_FOUND

    def post(self, request):
        self.data = request.data

        if not request.user.is_authenticated:
            return Response({"message": "Authentication credentials were not provided."},
                            status=status.HTTP_401_UNAUTHORIZED)

        if "id" in self.data:
            self.pk = self.data.get("id")

        if "action" in self.data:
            action = str(self.data["action"])
            action_mapper = {
                "postBilling": self.postBilling,
            }
            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST)
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST)
    
    def postBilling(self):
        try:
            # Extract fields from request
            patient = self.data.get("patient")
            prescriptionRecord = self.data.get("prescriptionRecord")
            # Numeric fields (default to 0 if not provided)
            first_check_up = int(self.data.get("first_check_up", 0))
            follow_up_check_up = int(self.data.get("follow_up_check_up", 0))
            one_month_late_check_up = int(self.data.get("one_month_late_check_up", 0))
            stress_test = int(self.data.get("stress_test", 0))
            ecg_test = int(self.data.get("ecg_test", 0))
            morning_ect_injection = int(self.data.get("morning_ect_injection", 0))
            injection_in_back = int(self.data.get("injection_in_back", 0))
            counselling_session = int(self.data.get("counselling_session", 0))
            evening_first_check_up = int(self.data.get("evening_first_check_up", 0))
            evening_follow_up_check_up = int(self.data.get("evening_follow_up_check_up", 0))
            special_appointment_check_up = int(self.data.get("special_appointment_check_up", 0))

            if not patient:
                self.ctx = {"message": "Patient ID is required."}
                self.status = status.HTTP_400_BAD_REQUEST
                return

            try:
                patient = Patient.objects.get(id=patient)
            except Patient.DoesNotExist:
                self.ctx = {"message": "Patient not found."}
                self.status = status.HTTP_404_NOT_FOUND
                return

            prescription_obj = None
            if prescriptionRecord:
                try:
                    prescription_obj = PrescriptionRecord.objects.get(id=prescriptionRecord)
                except PrescriptionRecord.DoesNotExist:
                    self.ctx = {"message": "Prescription not found."}
                    self.status = status.HTTP_404_NOT_FOUND
                    return

            # Create the PatientCharge object
            obj = PatientCharge.objects.create(
                patient=patient,
                prescriptionRecord=prescription_obj,
                first_check_up=first_check_up,
                follow_up_check_up=follow_up_check_up,
                one_month_late_check_up=one_month_late_check_up,
                stress_test=stress_test,
                ecg_test=ecg_test,
                morning_ect_injection=morning_ect_injection,
                injection_in_back=injection_in_back,
                counselling_session=counselling_session,
                evening_first_check_up=evening_first_check_up,
                evening_follow_up_check_up=evening_follow_up_check_up,
                special_appointment_check_up=special_appointment_check_up
            )

            serializer = PatientChargeSerializer(obj).data
            self.ctx = {"message": "Patient charge record created successfully!", "data": serializer}
            self.status = status.HTTP_201_CREATED

        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    
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
                "patchBilling": self.patchBilling,
                "patchTestFee":self.patchTestFee,

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
    
    def patchTestFee(self):
        try:
            clinic_charge = ClinicCharge.objects.last()
            if not clinic_charge:
                self.ctx = {"message": "No Clinic Charges Found"}
                self.status = status.HTTP_404_NOT_FOUND
                return

            serializer = ClinicChargeSerializer(clinic_charge, data=self.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                self.ctx = {"message": "Clinic Charges updated successfully", "data": serializer.data}
                self.status = status.HTTP_200_OK
            else:
                self.ctx = {"message": "Validation Failed", "errors": serializer.errors}
                self.status = status.HTTP_400_BAD_REQUEST
        except Exception as e:
            self.ctx = {"message": "Failed to update Clinic Charges", "error": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR

    def patchBilling(self):
        try:
            # Retrieve numeric charge values from input (can be 0 or more)
            first_check_up = self.data.get('first_check_up')
            follow_up_check_up = self.data.get('follow_up_check_up')
            one_month_late_check_up = self.data.get('one_month_late_check_up')
            stress_test = self.data.get('stress_test')
            ecg_test = self.data.get('ecg_test')
            morning_ect_injection = self.data.get('morning_ect_injection')
            injection_in_back = self.data.get('injection_in_back')
            counselling_session = self.data.get('counselling_session')
            evening_first_check_up = self.data.get('evening_first_check_up')
            evening_follow_up_check_up = self.data.get('evening_follow_up_check_up')
            special_appointment_check_up = self.data.get('special_appointment_check_up')
            patient = self.data.get('patient')
            prescriptionRecord = self.data.get("prescriptionRecord")

            # Find record by ID
            charges = PatientCharge.objects.filter(pk=self.id).first()
            if not charges:
                self.ctx = {"message": f"Billing record with id {self.id} not found!"}
                self.status = status.HTTP_404_NOT_FOUND
                return

            # Update numeric fields only if not None
            if first_check_up is not None:
                charges.first_check_up = int(first_check_up)
            if follow_up_check_up is not None:
                charges.follow_up_check_up = int(follow_up_check_up)
            if one_month_late_check_up is not None:
                charges.one_month_late_check_up = int(one_month_late_check_up)
            if stress_test is not None:
                charges.stress_test = int(stress_test)
            if ecg_test is not None:
                charges.ecg_test = int(ecg_test)
            if morning_ect_injection is not None:
                charges.morning_ect_injection = int(morning_ect_injection)
            if injection_in_back is not None:
                charges.injection_in_back = int(injection_in_back)
            if counselling_session is not None:
                charges.counselling_session = int(counselling_session)
            if evening_first_check_up is not None:
                charges.evening_first_check_up = int(evening_first_check_up)
            if evening_follow_up_check_up is not None:
                charges.evening_follow_up_check_up = int(evening_follow_up_check_up)
            if special_appointment_check_up is not None:
                charges.special_appointment_check_up = int(special_appointment_check_up)

            if prescriptionRecord is not None:
                try:
                    charges.prescriptionRecord = PrescriptionRecord.objects.get(pk=prescriptionRecord)
                except PrescriptionRecord.DoesNotExist:
                    self.ctx = {"message": "Invalid prescription record ID provided!"}
                    self.status = status.HTTP_400_BAD_REQUEST
                    return

            if patient is not None:
                try:
                    charges.patient = Patient.objects.get(pk=patient)
                except Patient.DoesNotExist:
                    self.ctx = {"message": "Invalid patient ID provided!"}
                    self.status = status.HTTP_400_BAD_REQUEST
                    return

            # Save changes
            charges.save()
            serializer = PatientChargeSerializer(charges).data
            self.ctx = {"message": "Billing record updated successfully!", "data": serializer}
            self.status = status.HTTP_200_OK

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
                "delBilling": self.delBilling
            }

            action_status = action_mapper.get(action)
            if action_status:
                action_status()
            else:
                return Response({"message": "Choose Wrong Option !", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
            return Response(self.ctx, self.status)
        else:
            return Response({"message": "Action is not in dict", "data": None}, status.HTTP_400_BAD_REQUEST) # noqa
    
    def delBilling(self):
        try:
            data = PatientCharge.objects.get(pk=self.id)
            if data:
                data.delete()
            self.ctx = {"message": "Patient Clinic Record deleted!"}
            self.status = status.HTTP_201_CREATED
        except PatientCharge.DoesNotExist:
            self.ctx = {"message": "Patient Clinic Record id Not Found!"}
            self.status = status.HTTP_404_NOT_FOUND
        except Exception as e:
            self.ctx = {"message": "Something went wrong!", "error_msg": str(e)}
            self.status = status.HTTP_500_INTERNAL_SERVER_ERROR
    

        

        


        
        
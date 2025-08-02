from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone number must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser):
    first_name = models.CharField(
        max_length=30,
        verbose_name="First Name"
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name="Last Name"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email Address"
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Phone Number"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Is Staff"
    )
    is_superuser = models.BooleanField(
        default=False,
        verbose_name="Is Superuser"
    )
    is_doctor = models.BooleanField(
        default=False,
        verbose_name="Is Doctor"
    )
    is_receptionist = models.BooleanField(
        default=False,
        verbose_name="Is Receptionist"
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date Created"
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Date Updated"
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'email']

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser or self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser or self.is_staff


class DoctorPersonalDetail(models.Model):
    """DoctorPersonalDetail model"""
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True,
        related_name="doctor_personal_detail"
    )

    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True
    )
    email = models.EmailField(
        verbose_name="Email", blank=True, null=True
    )
    profile_img = models.CharField(
        max_length=255, verbose_name="Profile Image", blank=True, null=True
    )
    highest_qualification = models.CharField(
        max_length=255, verbose_name="Highest Qualification",
        blank=True, null=True
    )
    hospital_address = models.CharField(
        max_length=255, verbose_name="Hospital Address", blank=True, null=True
    )
    medical_registration_number = models.CharField(
        max_length=255, verbose_name="Medical Registration Number",
        blank=True, null=True
    )
    graduation_year = models.CharField(
        max_length=4, verbose_name="Graduation Year", blank=True, null=True
    )
    specialty = models.CharField(
        max_length=255, verbose_name="Specialty", blank=True, null=True
    )
    date_created = models.DateTimeField(
        verbose_name="Date Created", auto_now_add=True
    )
    date_updated = models.DateTimeField(
        verbose_name="Date Update", auto_now=True
    )
    first_name = models.CharField(
        max_length=255, verbose_name="First Name", blank=True
    )
    last_name = models.CharField(
        max_length=255, verbose_name="Last Name", blank=True
    )
    phone_number = models.CharField(
        max_length=255, verbose_name="Phone Number", blank=True
    )
    status = models.CharField(
        max_length=255, verbose_name="status", blank=True
    )
    is_verified_doctor = models.BooleanField(
        default=False, verbose_name="Is Verified Doctor"
    )

    class Meta:
        """Meta Arguments"""
        db_table = 'doctor_personal_detail'

    def __str__(self):
        return f"{self.email}"

class Patient(models.Model):
    first_name = models.CharField(
        max_length=255, verbose_name="First Name", blank=True
    )
    middle_name = models.CharField(
        max_length=255, verbose_name="Last Name", blank=True, null=True,
    )
    last_name = models.CharField(
        max_length=255, verbose_name="Last Name", blank=True
    )
    phone = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Phone Number", blank=True,
        null=True
    )
    address = models.CharField(
        max_length=455, verbose_name="Address", blank=True, null=True
    )
    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date Created"
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Date Updated"
    )

    class Meta:
        db_table = "patient"
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f'{self.first_name} {self.middle_name or ""} {self.last_name}'

class Receptionist(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True,
        related_name="receptionist_profile"
    )
    user_created = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
    )
    first_name = models.CharField(
        max_length=255, verbose_name="First Name", blank=True
    )
    middle_name = models.CharField(
        max_length=255, verbose_name="Middle Name", blank=True, null=True
    )
    last_name = models.CharField(
        max_length=255, verbose_name="Last Name", blank=True
    )
    phone = models.CharField(
        max_length=15, verbose_name="Phone Number", blank=True, null=True
    )
    email = models.EmailField(
        verbose_name="Email", blank=True, null=True
    )
    date_created = models.DateTimeField(
        auto_now_add=True, verbose_name="Date Created"
    )
    date_updated = models.DateTimeField(
        auto_now=True, verbose_name="Date Updated"
    )

    class Meta:
        db_table = "receptionist"
        verbose_name = "Receptionist"
        verbose_name_plural = "Receptionists"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

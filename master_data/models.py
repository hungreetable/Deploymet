from django.db import models

# Create your models here.


class MedicineType(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name="Medicine Type Name"
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
        db_table = "MedicineType"
        verbose_name = "Medicine Type"
        verbose_name_plural = "Medicine Type"

    def __str__(self):
        return self.name


class GenericName(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name="Generic Name"
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
        db_table = "GenericName"
        verbose_name = "Generic Name"
        verbose_name_plural = "Generic Name"

    def __str__(self):
        return self.name


class MedicineData(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name="Medicine Name"
    )

    price = models.CharField(
        max_length=30,
        verbose_name="Price",
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(
        verbose_name="Quantity",
        default=0
    )

    medicine_type = models.ForeignKey(
        MedicineType,
        on_delete=models.CASCADE,
        verbose_name="Medicine Type"
        )

    generic_name = models.ForeignKey(
        GenericName,
        on_delete=models.CASCADE,
        verbose_name="Generic Name"
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
        db_table = "MedicineData"
        verbose_name = "Medicine Data"
        verbose_name_plural = "Medicine Data"

    def __str__(self):
        return self.name

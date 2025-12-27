from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    # owner == tu (Django User), jo tenant create karega
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='tenant_user')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tenants')

    name = models.CharField(max_length=100)          # tenant name
    room_no = models.CharField(max_length=20, unique=True)
    aadhar_no = models.CharField(max_length=12)
    address = models.TextField()
    mobile1 = models.CharField(max_length=15)
    mobile2 = models.CharField(max_length=15, blank=True)

    joining_date = models.DateField()                # open date
    open_unit = models.IntegerField(default=0)       # open unit
    base_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.room_no}"


class RentRecord(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='rents')
    month = models.CharField(max_length=20)          # e.g. "December 2025"
    year = models.IntegerField()
    rent_date = models.DateField()

    base_rent_amount = models.DecimalField(max_digits=10, decimal_places=2)

    open_unit = models.IntegerField(default=0)
    close_unit = models.IntegerField(null=True, blank=True)
    units_used = models.IntegerField(null=True, blank=True)

    bill_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    paid_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # units = close - open, bill = units * unit_rate (12 nahi, jo owner ne set kiya)
        if self.close_unit is not None and self.open_unit is not None:
            self.units_used = self.close_unit - self.open_unit
            self.bill_amount = self.units_used * self.tenant.unit_rate
        self.total_amount = self.base_rent_amount + self.bill_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant.name} - {self.month} {self.year}"

    class Meta:
        unique_together = ('tenant', 'month', 'year')

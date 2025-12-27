from datetime import date
from calendar import monthrange
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Tenant, RentRecord


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Owner (superuser / staff)
            if user.is_staff:
                return redirect('owner_dashboard')
            # Normal tenant
            return redirect('user_dashboard')

        messages.error(request, 'Invalid ID or password')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def owner_dashboard(request):
    # sirf owner (staff) ko access
    if not request.user.is_staff:
        return redirect('user_dashboard')

    # OWNER ADDS TENANT
    if request.method == 'POST' and 'add_tenant' in request.POST:
        name = (request.POST.get('name') or '').strip()
        room_no = (request.POST.get('room_no') or '').strip()
        aadhar_no = request.POST.get('aadhar_no')
        address = request.POST.get('address')
        mobile1 = request.POST.get('mobile1')
        mobile2 = request.POST.get('mobile2', '')
        joining_date = request.POST.get('joining_date')
        base_rent = float(request.POST.get('base_rent', 0) or 0)
        unit_rate = float(request.POST.get('unit_rate', 0) or 0)
        advance = float(request.POST.get('advance', 0) or 0)
        open_unit = int(request.POST.get('open_unit', 0) or 0)

        # USERNAME = room no, PASSWORD = name + @123
        # e.g. name = "Ravi Kumar" -> password "ravikumar@123"
        tenant_username = room_no.lower()
        tenant_password = f"{name.replace(' ', '').lower()}@123"

        if not tenant_username or not tenant_password:
            messages.error(request, "Name and Room No are required to generate login details.")
        else:
            try:
                user = User.objects.create_user(
                    username=tenant_username,
                    password=tenant_password,
                )
                Tenant.objects.create(
                    user=user,
                    owner=request.user,
                    name=name,
                    room_no=room_no,
                    aadhar_no=aadhar_no,
                    address=address,
                    mobile1=mobile1,
                    mobile2=mobile2,
                    joining_date=joining_date,
                    base_rent=base_rent,
                    unit_rate=unit_rate,
                    advance=advance,
                    open_unit=open_unit,
                )
                messages.success(
                    request,
                    f"Tenant {name} added. Username: {tenant_username} | Password: {tenant_password}"
                )
            except Exception as e:
                messages.error(request, f"Error creating tenant: {e}")

    tenants = Tenant.objects.filter(owner=request.user)
    return render(request, 'owner_dashboard.html', {'tenants': tenants})



@login_required
def user_dashboard(request):
    try:
        tenant = Tenant.objects.get(user=request.user)
    except Tenant.DoesNotExist:
        messages.error(request, 'No tenant data linked to your account.')
        return render(request, 'user_dashboard.html', {'error': 'No tenant data'})

    today = date.today()

    # joining_date se current month tak record generate
    y = tenant.joining_date.year
    m = tenant.joining_date.month

    previous_close = None

    while (y < today.year) or (y == today.year and m <= today.month):
        month_name = date(y, m, 1).strftime('%B %Y')

        rent, created = RentRecord.objects.get_or_create(
            tenant=tenant,
            month=month_name,
            year=y,
            defaults={
                'rent_date': date(y, m, monthrange(y, m)[1]),
                'base_rent_amount': tenant.base_rent,
                'open_unit': tenant.open_unit if previous_close is None else previous_close,
                'status': 'Pending',
            }
        )

        # agar existing hai aur previous_close set hai, ensure open_unit chain
        if not created and previous_close is not None and rent.open_unit != previous_close:
            rent.open_unit = previous_close
            rent.save()

        if rent.close_unit is not None:
            previous_close = rent.close_unit
        elif previous_close is None:
            previous_close = rent.open_unit

        m += 1
        if m > 12:
            m = 1
            y += 1

    rents = tenant.rents.order_by('rent_date')
    total_rent = sum(r.base_rent_amount for r in rents)
    total_bill = sum(r.bill_amount for r in rents)
    grand_total = sum(r.total_amount for r in rents)

    return render(request, 'user_dashboard.html', {
        'tenant': tenant,
        'rents': rents,
        'total_rent': total_rent,
        'total_bill': total_bill,
        'grand_total': grand_total,
    })


from datetime import date
...
@login_required
def payment_page(request, rent_id):
    tenant = get_object_or_404(Tenant, user=request.user)
    rent = get_object_or_404(RentRecord, id=rent_id, tenant=tenant)
    
    # If already paid, show success
    if rent.status == 'Paid':
        return render(request, 'payment_page.html', {'rent': rent, 'success': True})
    
    # Handle unit entry if not set
    if rent.close_unit is None:
        if request.method == 'POST' and 'set_units' in request.POST:
            close_unit = request.POST.get('close_unit')
            if not close_unit:
                messages.error(request, 'Please enter current meter reading (close unit).')
                return render(request, 'payment_page.html', {'rent': rent, 'ask_units': True})
            
            rent.close_unit = int(close_unit)
            if rent.open_unit is None:
                rent.open_unit = 0
            rent.save()  # This auto-calculates units_used, bill_amount, total_amount
            messages.success(request, 'Units updated. Now scan QR to pay.')
        
        return render(request, 'payment_page.html', {'rent': rent, 'ask_units': True})
    
    # QR Scan & Auto-Payment Confirmation (NEW AUTO SUCCESS FLOW)
    if request.method == 'POST' and 'upi_success' in request.POST:
        # Simulate UPI success - in production, verify with UPI API
        rent.status = 'Paid'
        rent.paid_date = date.today()
        rent.save()
        messages.success(request, 'Payment received successfully via UPI!')
        return render(request, 'payment_page.html', {'rent': rent, 'success': True})
    
    # Show QR for payment (total_amount auto-calculated)
    payable = rent.total_amount
    return render(request, 'payment_page.html', {'rent': rent, 'payable': payable})



from django.db.models import Sum

def owner_tenant_detail(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)

    # saare records table ke liye
    rents = RentRecord.objects.filter(tenant=tenant).order_by('rent_date')

    # SIRF paid records se totals
    paid_qs = rents.filter(status='Paid')
    total_rent = paid_qs.aggregate(s=Sum('base_rent_amount'))['s'] or 0
    total_bill = paid_qs.aggregate(s=Sum('bill_amount'))['s'] or 0
    total_paid = paid_qs.aggregate(s=Sum('total_amount'))['s'] or 0

    context = {
        'tenant': tenant,
        'rents': rents,
        'total_rent': total_rent,
        'total_bill': total_bill,
        'total_paid': total_paid,
    }
    return render(request, 'owner_tenant_detail.html', context)





@login_required
def edit_profile(request):
    if request.user.is_staff:
        return redirect('owner_dashboard')

    tenant = Tenant.objects.get(user=request.user)

    if request.method == 'POST':
        tenant.name = request.POST.get('name')
        tenant.mobile1 = request.POST.get('mobile1')
        tenant.address = request.POST.get('address')
        tenant.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_dashboard')

    # same template, edit_mode flag ke sath
    rents = tenant.rents.order_by('-rent_date')
    total_rent = sum(r.base_rent_amount for r in rents)
    total_bill = sum(r.bill_amount for r in rents)
    grand_total = sum(r.total_amount for r in rents)

    return render(request, 'user_dashboard.html', {
        'tenant': tenant,
        'rents': rents,
        'total_rent': total_rent,
        'total_bill': total_bill,
        'grand_total': grand_total,
        'edit_mode': True,
    })

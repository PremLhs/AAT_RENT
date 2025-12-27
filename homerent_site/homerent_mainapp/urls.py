from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('owner-dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('owner-tenant/<int:tenant_id>/', views.owner_tenant_detail, name='owner_tenant_detail'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('payment/<int:rent_id>/', views.payment_page, name='payment_page'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),  # <-- new
]

# client/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('search_details/', views.search_details, name='search_details'),
    path('search_company/', views.search_company, name='search_company'), 
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('client_list/', views.client_list, name='client_list'),
    path('add/', views.client_add, name='client_add'),
    path('edit/<int:pk>/', views.client_update, name='client_update'),
    path('delete/<int:pk>/', views.client_delete_select, name='client_delete_select'),
    path('signup/', views.signup_view, name='signup'),
    path('import_excel/', views.import_excel, name='import_excel'),
    path('export_excel/<str:list_type>/', views.export_excel, name='export_excel'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]
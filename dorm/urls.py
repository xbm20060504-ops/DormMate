from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Rooms
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/join/', views.room_join, name='room_join'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/edit/', views.room_edit, name='room_edit'),

    # Resources & Bookings
    path('rooms/<int:room_pk>/resources/create/', views.resource_create, name='resource_create'),
    path('resources/<int:pk>/schedule/', views.resource_schedule, name='resource_schedule'),
    path('resources/<int:resource_pk>/book/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='booking_cancel'),

    # Chores
    path('rooms/<int:room_pk>/chores/', views.chore_list, name='chore_list'),
    path('rooms/<int:room_pk>/chores/create/', views.chore_create, name='chore_create'),
    path('rooms/<int:room_pk>/chores/assign/', views.chore_assign, name='chore_assign'),
    path('rooms/<int:room_pk>/chores/auto-rotate/', views.chore_auto_rotate, name='chore_auto_rotate'),
    path('chores/<int:pk>/complete/', views.chore_complete, name='chore_complete'),

    # Expenses
    path('rooms/<int:room_pk>/expenses/', views.expense_list, name='expense_list'),
    path('rooms/<int:room_pk>/expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/settle/', views.expense_settle, name='expense_settle'),

    # Announcements
    path('rooms/<int:room_pk>/announcements/', views.announcement_list, name='announcement_list'),
    path('rooms/<int:room_pk>/announcements/create/', views.announcement_create, name='announcement_create'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),

    # Analytics
    path('rooms/<int:room_pk>/analytics/', views.analytics, name='analytics'),
]

from django.contrib import admin
from .models import Room, Resource, Booking, Chore, ChoreAssignment, Expense, Announcement, ActivityLog


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'owner', 'member_count', 'capacity', 'invite_code']
    list_filter = ['building', 'floor']
    search_fields = ['name', 'building']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'room', 'slot_duration_minutes']
    list_filter = ['category']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'date', 'start_time', 'end_time', 'status']
    list_filter = ['status', 'date']


@admin.register(Chore)
class ChoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'room', 'frequency']
    list_filter = ['frequency']


@admin.register(ChoreAssignment)
class ChoreAssignmentAdmin(admin.ModelAdmin):
    list_display = ['chore', 'assigned_to', 'due_date', 'status']
    list_filter = ['status', 'due_date']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'paid_by', 'room', 'is_settled', 'date']
    list_filter = ['category', 'is_settled']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'room', 'author', 'priority', 'is_pinned', 'created_at']
    list_filter = ['priority', 'is_pinned']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_type', 'target_name', 'timestamp']
    list_filter = ['action', 'timestamp']

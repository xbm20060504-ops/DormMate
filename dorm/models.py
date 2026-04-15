from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import math


class Room(models.Model):
    """A dormitory room with multiple residents."""
    name = models.CharField(max_length=100, help_text='e.g., Room 301-A')
    building = models.CharField(max_length=100, default='Main Building')
    floor = models.PositiveIntegerField(default=1)
    capacity = models.PositiveIntegerField(default=4)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_rooms',
                              help_text='Room creator / admin')
    members = models.ManyToManyField(User, related_name='joined_rooms', blank=True)
    invite_code = models.CharField(max_length=8, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['building', 'floor', 'name']

    def __str__(self):
        return f"{self.name} ({self.building})"

    def save(self, *args, **kwargs):
        if not self.invite_code:
            import random, string
            self.invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    @property
    def member_count(self):
        return self.members.count()

    @property
    def is_full(self):
        return self.member_count >= self.capacity


class Resource(models.Model):
    """A shared resource in the dormitory that can be booked."""
    CATEGORY_CHOICES = [
        ('LAUNDRY', 'Washing Machine / Dryer'),
        ('KITCHEN', 'Kitchen / Cooking'),
        ('BATHROOM', 'Bathroom / Shower'),
        ('STUDY', 'Study Room'),
        ('GAME', 'Game Room / Lounge'),
        ('OTHER', 'Other'),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='OTHER')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='resources')
    description = models.TextField(blank=True)
    slot_duration_minutes = models.PositiveIntegerField(default=60,
                                                        help_text='Duration of each booking slot in minutes')
    available_from = models.TimeField(default='07:00')
    available_until = models.TimeField(default='23:00')
    icon = models.CharField(max_length=50, default='bi-box', help_text='Bootstrap icon class')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    @property
    def category_color(self):
        colors = {
            'LAUNDRY': '#3B82F6',
            'KITCHEN': '#F59E0B',
            'BATHROOM': '#06B6D4',
            'STUDY': '#8B5CF6',
            'GAME': '#EC4899',
            'OTHER': '#6B7280',
        }
        return colors.get(self.category, '#6B7280')


class Booking(models.Model):
    """A time-slot booking for a shared resource."""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.resource.name} - {self.user.username} ({self.date} {self.start_time})"

    @property
    def is_past(self):
        now = timezone.localtime(timezone.now())
        booking_end = timezone.datetime.combine(self.date, self.end_time)
        return now.replace(tzinfo=None) > booking_end

    @property
    def is_ongoing(self):
        now = timezone.localtime(timezone.now())
        booking_start = timezone.datetime.combine(self.date, self.start_time)
        booking_end = timezone.datetime.combine(self.date, self.end_time)
        return booking_start <= now.replace(tzinfo=None) <= booking_end


class Chore(models.Model):
    """A recurring chore/task in the dormitory."""
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('BIWEEKLY', 'Every 2 Weeks'),
        ('MONTHLY', 'Monthly'),
    ]
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='chores')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='WEEKLY')
    icon = models.CharField(max_length=50, default='bi-check2-square')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ChoreAssignment(models.Model):
    """An assignment of a chore to a specific member for a specific period."""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('DONE', 'Done'),
        ('SKIPPED', 'Skipped'),
    ]
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name='assignments')
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chore_assignments')
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date', 'chore__name']

    def __str__(self):
        return f"{self.chore.name} → {self.assigned_to.username} (due {self.due_date})"

    @property
    def is_overdue(self):
        return self.status == 'PENDING' and self.due_date < timezone.now().date()

    def save(self, *args, **kwargs):
        if self.status == 'DONE' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != 'DONE':
            self.completed_at = None
        super().save(*args, **kwargs)


class Expense(models.Model):
    """A shared expense among room members."""
    CATEGORY_CHOICES = [
        ('UTILITY', 'Utilities (Water/Electric)'),
        ('SUPPLY', 'Supplies (Toilet Paper, etc.)'),
        ('FOOD', 'Shared Food / Groceries'),
        ('REPAIR', 'Repair / Maintenance'),
        ('OTHER', 'Other'),
    ]
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='OTHER')
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='expenses')
    split_among = models.ManyToManyField(User, related_name='expenses_shared')
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.now)
    is_settled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - MOP {self.amount}"

    @property
    def per_person_amount(self):
        count = self.split_among.count()
        if count == 0:
            return self.amount
        return math.ceil(self.amount / count * 100) / 100  # round up to 2 decimals


class Announcement(models.Model):
    """Room announcements / notice board."""
    PRIORITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('URGENT', 'Urgent'),
    ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='announcements')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='INFO')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    """Tracks all activities for audit trail."""
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('COMPLETE', 'Completed'),
        ('BOOK', 'Booked'),
        ('CANCEL', 'Cancelled'),
        ('JOIN', 'Joined'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    target_type = models.CharField(max_length=50)
    target_name = models.CharField(max_length=300)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} {self.target_type}: {self.target_name}"

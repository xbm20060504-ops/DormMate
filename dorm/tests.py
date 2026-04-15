from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date, time, timedelta
from decimal import Decimal
from .models import Room, Resource, Booking, Chore, ChoreAssignment, Expense, Announcement


class RoomModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.room = Room.objects.create(name='Room 301', building='Building A', owner=self.user, capacity=4)
        self.room.members.add(self.user)

    def test_room_creation(self):
        self.assertEqual(str(self.room), 'Room 301 (Building A)')
        self.assertEqual(len(self.room.invite_code), 8)

    def test_member_count(self):
        self.assertEqual(self.room.member_count, 1)

    def test_is_full(self):
        self.assertFalse(self.room.is_full)
        for i in range(3):
            u = User.objects.create_user(username=f'user{i}', password='pass123')
            self.room.members.add(u)
        self.assertTrue(self.room.is_full)


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.room = Room.objects.create(name='Room 301', owner=self.user)
        self.resource = Resource.objects.create(
            name='Washing Machine', category='LAUNDRY', room=self.room
        )

    def test_booking_creation(self):
        booking = Booking.objects.create(
            resource=self.resource, user=self.user,
            date=date.today(), start_time=time(10, 0), end_time=time(11, 0)
        )
        self.assertEqual(booking.status, 'ACTIVE')

    def test_past_booking(self):
        past_date = date.today() - timedelta(days=1)
        booking = Booking.objects.create(
            resource=self.resource, user=self.user,
            date=past_date, start_time=time(10, 0), end_time=time(11, 0)
        )
        self.assertTrue(booking.is_past)


class ChoreAssignmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.room = Room.objects.create(name='Room 301', owner=self.user)
        self.chore = Chore.objects.create(name='Clean bathroom', room=self.room)

    def test_overdue_detection(self):
        assignment = ChoreAssignment.objects.create(
            chore=self.chore, assigned_to=self.user,
            due_date=date.today() - timedelta(days=1)
        )
        self.assertTrue(assignment.is_overdue)

    def test_not_overdue_when_done(self):
        assignment = ChoreAssignment.objects.create(
            chore=self.chore, assigned_to=self.user,
            due_date=date.today() - timedelta(days=1),
            status='DONE'
        )
        self.assertFalse(assignment.is_overdue)

    def test_completed_at_auto_set(self):
        assignment = ChoreAssignment.objects.create(
            chore=self.chore, assigned_to=self.user,
            due_date=date.today()
        )
        self.assertIsNone(assignment.completed_at)
        assignment.status = 'DONE'
        assignment.save()
        self.assertIsNotNone(assignment.completed_at)


class ExpenseModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.room = Room.objects.create(name='Room 301', owner=self.user1)

    def test_per_person_amount(self):
        expense = Expense.objects.create(
            title='Electricity', amount=Decimal('100.00'),
            paid_by=self.user1, room=self.room
        )
        expense.split_among.set([self.user1, self.user2])
        self.assertEqual(expense.per_person_amount, 50.0)

    def test_per_person_odd_split(self):
        user3 = User.objects.create_user(username='user3', password='pass123')
        expense = Expense.objects.create(
            title='Water', amount=Decimal('100.00'),
            paid_by=self.user1, room=self.room
        )
        expense.split_among.set([self.user1, self.user2, user3])
        # 100 / 3 = 33.33... rounded up to 33.34
        self.assertGreaterEqual(expense.per_person_amount, 33.33)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_room_create(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('room_create'), {
            'name': 'Room 501', 'building': 'Building B',
            'floor': 5, 'capacity': 4,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Room.objects.filter(name='Room 501').exists())

    def test_room_join_with_code(self):
        room = Room.objects.create(name='Room 301', owner=self.user, invite_code='ABCD1234')
        user2 = User.objects.create_user(username='user2', password='pass123')
        self.client.login(username='user2', password='pass123')
        response = self.client.post(reverse('room_join'), {'invite_code': 'ABCD1234'})
        self.assertEqual(response.status_code, 302)
        self.assertIn(user2, room.members.all())

    def test_booking_conflict_detection(self):
        self.client.login(username='testuser', password='testpass123')
        room = Room.objects.create(name='R1', owner=self.user)
        room.members.add(self.user)
        resource = Resource.objects.create(name='WM', room=room, category='LAUNDRY')
        # Create first booking
        Booking.objects.create(
            resource=resource, user=self.user,
            date=date.today() + timedelta(days=1),
            start_time=time(10, 0), end_time=time(11, 0)
        )
        # Try conflicting booking
        response = self.client.post(
            reverse('booking_create', kwargs={'resource_pk': resource.pk}),
            {'date': (date.today() + timedelta(days=1)).isoformat(),
             'start_time': '10:30', 'end_time': '11:30', 'note': ''}
        )
        # Should show error, not redirect
        self.assertEqual(response.status_code, 200)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, date

from .models import (
    Room, Resource, Booking, Chore, ChoreAssignment,
    Expense, Announcement, ActivityLog
)
from .forms import (
    CustomUserCreationForm, RoomForm, ResourceForm, BookingForm,
    ChoreForm, ChoreAssignmentForm, ExpenseForm, AnnouncementForm,
    JoinRoomForm
)


# ─── Auth ─────────────────────────────────────────────
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to DormMate, {user.first_name}!')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# ─── Dashboard ────────────────────────────────────────
@login_required
def dashboard(request):
    user = request.user
    rooms = Room.objects.filter(Q(owner=user) | Q(members=user)).distinct()
    current_room = rooms.first()

    context = {
        'rooms': rooms,
        'current_room': current_room,
    }

    if current_room:
        today = timezone.now().date()
        # Today's bookings
        todays_bookings = Booking.objects.filter(
            resource__room=current_room, date=today, status='ACTIVE'
        )[:5]
        # My pending chores
        my_chores = ChoreAssignment.objects.filter(
            assigned_to=user, chore__room=current_room, status='PENDING'
        )[:5]
        # Overdue chores
        overdue_chores = ChoreAssignment.objects.filter(
            assigned_to=user, chore__room=current_room,
            status='PENDING', due_date__lt=today
        ).count()
        # Unsettled expenses
        unsettled_expenses = Expense.objects.filter(
            room=current_room, is_settled=False
        )
        total_unsettled = unsettled_expenses.aggregate(t=Sum('amount'))['t'] or 0
        # Announcements
        announcements = Announcement.objects.filter(room=current_room)[:3]
        # Recent activity
        activities = ActivityLog.objects.filter(room=current_room)[:10]
        # Stats
        stats = {
            'members': current_room.member_count,
            'resources': current_room.resources.count(),
            'pending_chores': ChoreAssignment.objects.filter(
                chore__room=current_room, status='PENDING'
            ).count(),
            'overdue_chores': overdue_chores,
            'unsettled_amount': total_unsettled,
        }
        context.update({
            'todays_bookings': todays_bookings,
            'my_chores': my_chores,
            'announcements': announcements,
            'activities': activities,
            'stats': stats,
        })

    return render(request, 'dorm/dashboard.html', context)


# ─── Room Management ──────────────────────────────────
@login_required
def room_create(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.owner = request.user
            room.save()
            room.members.add(request.user)
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Room', target_name=room.name, room=room
            )
            messages.success(request, f'Room "{room.name}" created! Invite code: {room.invite_code}')
            return redirect('room_detail', pk=room.pk)
    else:
        form = RoomForm()
    return render(request, 'dorm/room_form.html', {'form': form, 'title': 'Create Room'})


@login_required
def room_join(request):
    if request.method == 'POST':
        form = JoinRoomForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['invite_code'].upper()
            try:
                room = Room.objects.get(invite_code=code)
                if request.user in room.members.all():
                    messages.info(request, 'You are already in this room.')
                elif room.is_full:
                    messages.error(request, 'This room is full.')
                else:
                    room.members.add(request.user)
                    ActivityLog.objects.create(
                        user=request.user, action='JOIN',
                        target_type='Room', target_name=room.name, room=room
                    )
                    messages.success(request, f'You joined "{room.name}"!')
                return redirect('room_detail', pk=room.pk)
            except Room.DoesNotExist:
                messages.error(request, 'Invalid invite code.')
    else:
        form = JoinRoomForm()
    return render(request, 'dorm/room_join.html', {'form': form})


@login_required
def room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.user != room.owner and request.user not in room.members.all():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    context = {
        'room': room,
        'members': room.members.all(),
        'resources': room.resources.all(),
        'chores': room.chores.all(),
    }
    return render(request, 'dorm/room_detail.html', context)


@login_required
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated.')
            return redirect('room_detail', pk=room.pk)
    else:
        form = RoomForm(instance=room)
    return render(request, 'dorm/room_form.html', {'form': form, 'title': 'Edit Room'})


# ─── Resources & Bookings ────────────────────────────
@login_required
def resource_create(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    if request.method == 'POST':
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.room = room
            resource.save()
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Resource', target_name=resource.name, room=room
            )
            messages.success(request, f'Resource "{resource.name}" added!')
            return redirect('room_detail', pk=room.pk)
    else:
        form = ResourceForm()
    return render(request, 'dorm/resource_form.html', {'form': form, 'room': room})


@login_required
def resource_schedule(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    room = resource.room
    # Show bookings for next 7 days
    today = timezone.now().date()
    selected_date = request.GET.get('date', '')
    if selected_date:
        try:
            selected_date = date.fromisoformat(selected_date)
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    dates = [today + timedelta(days=i) for i in range(7)]
    bookings = Booking.objects.filter(
        resource=resource, date=selected_date, status='ACTIVE'
    )

    context = {
        'resource': resource,
        'room': room,
        'dates': dates,
        'selected_date': selected_date,
        'bookings': bookings,
    }
    return render(request, 'dorm/resource_schedule.html', context)


@login_required
def booking_create(request, resource_pk):
    resource = get_object_or_404(Resource, pk=resource_pk)
    room = resource.room

    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.resource = resource
            booking.user = request.user
            # Check for conflicts
            conflicts = Booking.objects.filter(
                resource=resource, date=booking.date, status='ACTIVE'
            ).filter(
                Q(start_time__lt=booking.end_time, end_time__gt=booking.start_time)
            )
            if conflicts.exists():
                messages.error(request, 'Time slot conflict! Please choose a different time.')
            else:
                booking.save()
                ActivityLog.objects.create(
                    user=request.user, action='BOOK',
                    target_type='Resource', target_name=resource.name, room=room
                )
                messages.success(request, f'Booked {resource.name} successfully!')
                return redirect('resource_schedule', pk=resource.pk)
    else:
        initial_date = request.GET.get('date', timezone.now().date().isoformat())
        form = BookingForm(initial={'date': initial_date})

    return render(request, 'dorm/booking_form.html', {
        'form': form, 'resource': resource, 'room': room
    })


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        booking.status = 'CANCELLED'
        booking.save()
        ActivityLog.objects.create(
            user=request.user, action='CANCEL',
            target_type='Booking', target_name=booking.resource.name,
            room=booking.resource.room
        )
        messages.success(request, 'Booking cancelled.')
    return redirect('resource_schedule', pk=booking.resource.pk)


# ─── Chores ───────────────────────────────────────────
@login_required
def chore_list(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    chores = room.chores.all()
    today = timezone.now().date()
    pending = ChoreAssignment.objects.filter(chore__room=room, status='PENDING')
    completed = ChoreAssignment.objects.filter(
        chore__room=room, status='DONE',
        completed_at__gte=timezone.now() - timedelta(days=7)
    )
    context = {
        'room': room, 'chores': chores,
        'pending_assignments': pending,
        'completed_assignments': completed,
    }
    return render(request, 'dorm/chore_list.html', context)


@login_required
def chore_create(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    if request.method == 'POST':
        form = ChoreForm(request.POST)
        if form.is_valid():
            chore = form.save(commit=False)
            chore.room = room
            chore.save()
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Chore', target_name=chore.name, room=room
            )
            messages.success(request, f'Chore "{chore.name}" created!')
            return redirect('chore_list', room_pk=room.pk)
    else:
        form = ChoreForm()
    return render(request, 'dorm/chore_form.html', {'form': form, 'room': room, 'title': 'Add Chore'})


@login_required
def chore_assign(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    if request.method == 'POST':
        form = ChoreAssignmentForm(request.POST, room=room)
        if form.is_valid():
            assignment = form.save()
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Chore Assignment',
                target_name=f"{assignment.chore.name} → {assignment.assigned_to.username}",
                room=room
            )
            messages.success(request, 'Chore assigned!')
            return redirect('chore_list', room_pk=room.pk)
    else:
        form = ChoreAssignmentForm(room=room)
    return render(request, 'dorm/chore_assign_form.html', {'form': form, 'room': room})


@login_required
def chore_complete(request, pk):
    assignment = get_object_or_404(ChoreAssignment, pk=pk, assigned_to=request.user)
    assignment.status = 'DONE'
    assignment.save()
    ActivityLog.objects.create(
        user=request.user, action='COMPLETE',
        target_type='Chore', target_name=assignment.chore.name,
        room=assignment.chore.room
    )
    messages.success(request, f'"{assignment.chore.name}" marked as done!')
    return redirect('chore_list', room_pk=assignment.chore.room.pk)


@login_required
def chore_auto_rotate(request, room_pk):
    """Auto-generate chore assignments using round-robin rotation."""
    room = get_object_or_404(Room, pk=room_pk, owner=request.user)
    members = list(room.members.all())
    chores = list(room.chores.all())
    today = timezone.now().date()

    if not members or not chores:
        messages.error(request, 'Need at least one member and one chore to auto-rotate.')
        return redirect('chore_list', room_pk=room.pk)

    created_count = 0
    for i, chore in enumerate(chores):
        # Check if there's already a pending assignment for this chore
        existing = ChoreAssignment.objects.filter(
            chore=chore, status='PENDING', due_date__gte=today
        ).exists()
        if existing:
            continue

        # Round-robin: assign to next member
        member_index = i % len(members)
        freq_days = {'DAILY': 1, 'WEEKLY': 7, 'BIWEEKLY': 14, 'MONTHLY': 30}
        due = today + timedelta(days=freq_days.get(chore.frequency, 7))

        ChoreAssignment.objects.create(
            chore=chore,
            assigned_to=members[member_index],
            due_date=due,
        )
        created_count += 1

    messages.success(request, f'Auto-rotated {created_count} chore assignments!')
    return redirect('chore_list', room_pk=room.pk)


# ─── Expenses ─────────────────────────────────────────
@login_required
def expense_list(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    expenses = Expense.objects.filter(room=room)
    unsettled = expenses.filter(is_settled=False)
    settled = expenses.filter(is_settled=True)

    # Calculate balances
    balances = {}
    for member in room.members.all():
        paid = expenses.filter(paid_by=member, is_settled=False).aggregate(t=Sum('amount'))['t'] or 0
        owed = sum(
            e.per_person_amount for e in unsettled if member in e.split_among.all()
        )
        balances[member] = {
            'paid': float(paid),
            'owed': float(owed),
            'net': float(paid) - float(owed),
        }

    context = {
        'room': room,
        'unsettled': unsettled,
        'settled': settled[:10],
        'balances': balances,
        'total_unsettled': unsettled.aggregate(t=Sum('amount'))['t'] or 0,
    }
    return render(request, 'dorm/expense_list.html', context)


@login_required
def expense_create(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.paid_by = request.user
            expense.room = room
            expense.save()
            # Default: split among all members
            expense.split_among.set(room.members.all())
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Expense', target_name=f"{expense.title} (MOP {expense.amount})",
                room=room
            )
            messages.success(request, f'Expense "{expense.title}" added!')
            return redirect('expense_list', room_pk=room.pk)
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})
    return render(request, 'dorm/expense_form.html', {'form': form, 'room': room})


@login_required
def expense_settle(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.is_settled = True
    expense.save()
    messages.success(request, f'Expense "{expense.title}" marked as settled.')
    return redirect('expense_list', room_pk=expense.room.pk)


# ─── Announcements ────────────────────────────────────
@login_required
def announcement_list(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    announcements = Announcement.objects.filter(room=room)
    return render(request, 'dorm/announcement_list.html', {
        'room': room, 'announcements': announcements
    })


@login_required
def announcement_create(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.room = room
            ann.author = request.user
            ann.save()
            ActivityLog.objects.create(
                user=request.user, action='CREATE',
                target_type='Announcement', target_name=ann.title, room=room
            )
            messages.success(request, 'Announcement posted!')
            return redirect('announcement_list', room_pk=room.pk)
    else:
        form = AnnouncementForm()
    return render(request, 'dorm/announcement_form.html', {'form': form, 'room': room})


@login_required
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    room_pk = ann.room.pk
    if request.user == ann.author or request.user == ann.room.owner:
        ann.delete()
        messages.success(request, 'Announcement deleted.')
    return redirect('announcement_list', room_pk=room_pk)


# ─── Analytics ────────────────────────────────────────
@login_required
def analytics(request, room_pk):
    room = get_object_or_404(Room, pk=room_pk)
    members = room.members.all()

    # Chore stats per member
    chore_stats = []
    for m in members:
        total = ChoreAssignment.objects.filter(chore__room=room, assigned_to=m).count()
        done = ChoreAssignment.objects.filter(chore__room=room, assigned_to=m, status='DONE').count()
        chore_stats.append({
            'name': m.get_full_name() or m.username,
            'total': total, 'done': done,
            'rate': int(done / total * 100) if total > 0 else 0,
        })

    # Expense stats per member
    expense_stats = []
    for m in members:
        paid = Expense.objects.filter(room=room, paid_by=m).aggregate(t=Sum('amount'))['t'] or 0
        expense_stats.append({
            'name': m.get_full_name() or m.username,
            'paid': float(paid),
        })

    # Resource usage per category
    resource_usage = {}
    for cat_code, cat_label in Resource.CATEGORY_CHOICES:
        count = Booking.objects.filter(
            resource__room=room, resource__category=cat_code,
            status='ACTIVE'
        ).count()
        if count > 0:
            resource_usage[cat_label] = count

    # Expense by category
    expense_by_cat = {}
    for cat_code, cat_label in Expense.CATEGORY_CHOICES:
        total = Expense.objects.filter(
            room=room, category=cat_code
        ).aggregate(t=Sum('amount'))['t'] or 0
        if total > 0:
            expense_by_cat[cat_label] = float(total)

    context = {
        'room': room,
        'chore_stats': chore_stats,
        'expense_stats': expense_stats,
        'resource_usage': resource_usage,
        'expense_by_cat': expense_by_cat,
    }
    return render(request, 'dorm/analytics.html', context)

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Resource, Booking, Chore, ChoreAssignment, Expense, Announcement


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'building', 'floor', 'capacity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Room 301-A'}),
            'building': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Building C'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['name', 'category', 'description', 'slot_duration_minutes', 'available_from', 'available_until']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Washing Machine #1'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 15, 'max': 240}),
            'available_from': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'available_until': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['date', 'start_time', 'end_time', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError('End time must be after start time.')
        return cleaned_data


class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore
        fields = ['name', 'description', 'frequency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Clean common area'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class ChoreAssignmentForm(forms.ModelForm):
    class Meta:
        model = ChoreAssignment
        fields = ['chore', 'assigned_to', 'due_date']
        widgets = {
            'chore': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, room=None, **kwargs):
        super().__init__(*args, **kwargs)
        if room:
            self.fields['chore'].queryset = Chore.objects.filter(room=room)
            self.fields['assigned_to'].queryset = room.members.all()


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'description', 'date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electricity bill March'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class JoinRoomForm(forms.Form):
    invite_code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 8-character invite code'
        })
    )

from django.db.models import Q
from .models import Room


def room_context(request):
    """Make current room available to all templates."""
    if request.user.is_authenticated:
        rooms = Room.objects.filter(
            Q(owner=request.user) | Q(members=request.user)
        ).distinct()
        current_room = rooms.first()
        return {
            'current_room': current_room,
            'user_rooms': rooms,
        }
    return {}

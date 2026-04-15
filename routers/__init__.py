# routers package
from . import auth
from . import users
from . import dashboard
from . import records
from . import vitals
from . import medications
from . import appointments
from . import notifications
from . import bookings
from . import video
from . import admin
from . import chatbot

__all__ = [
    "auth",
    "users",
    "dashboard",
    "records",
    "vitals",
    "medications",
    "appointments",
    "notifications",
    "bookings",
    "video",
    "admin",
    "chatbot",
]


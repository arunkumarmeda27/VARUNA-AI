"""
VARUNA-AI: Dashboard URL Routing
"""

from django.urls import path
from dashboard import views

urlpatterns = [
    path("", views.dashboard_index, name="dashboard_home"),
]

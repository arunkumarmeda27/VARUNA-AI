"""
VARUNA-AI: Dashboard URL Routing
"""

from django.urls import path
from dashboard import views

urlpatterns = [
    path("", views.login_view, name="root_login"),
    path("login/", views.login_view, name="dashboard_login"),
    path("dashboard/", views.dashboard_index, name="dashboard_home"),
]


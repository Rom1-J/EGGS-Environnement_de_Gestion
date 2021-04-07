from django.urls import path
from . import views

app_name = "manager"
urlpatterns = [
    path('dashboard/', views.dashboard, name="dashboard"),
    path('contact/', views.contact, name="contact"),
]

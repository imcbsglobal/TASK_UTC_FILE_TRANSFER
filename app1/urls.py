from django.urls import path
from . import views

urlpatterns = [
    path("transfer/", views.transfer_api, name="transfer_api"),
    path("transfer-status-update/", views.transfer_status_update_api, name="transfer_status_update"),
    path("", views.transfer_page, name="transfer_view"),
]

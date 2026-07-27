from django.urls import path

from .views import AirtimeTransactionListView, GiftAirtimeView

app_name = "airtime"

urlpatterns = [
    path("airtime/gift/", GiftAirtimeView.as_view(), name="gift"),
    path("airtime/transactions/", AirtimeTransactionListView.as_view(), name="transaction-list"),
]

from django.urls import path

from .views import InterestListView, MyProfileView, PublicProfileView

app_name = "profiles"

urlpatterns = [
    path("profile/", MyProfileView.as_view(), name="my-profile"),
    path("profile/<uuid:user_id>/", PublicProfileView.as_view(), name="public-profile"),
    path("interests/", InterestListView.as_view(), name="interest-list"),
]

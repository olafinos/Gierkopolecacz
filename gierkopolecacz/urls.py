from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from .views import SignupView, LogoutView, ActivateView

urlpatterns = [
    path("", lambda req: redirect("/polecacz/")),
    path("polecacz/", include("polecacz.urls")),
    path("admin/", admin.site.urls),
    path("", include("django.contrib.auth.urls")),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("activate/<uidb64>/<token>/", ActivateView.as_view(), name="activate"),
    path("", include("pwa.urls"))
]

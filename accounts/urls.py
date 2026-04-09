from django.urls import path

from accounts.views import AdminProbeView, CsrfTokenView, LoginView, LogoutView, MeView, RegisterView


urlpatterns = [
    path("csrf", CsrfTokenView.as_view(), name="auth-csrf"),
    path("register", RegisterView.as_view(), name="auth-register"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
    path("me", MeView.as_view(), name="auth-me"),
    path("admin-probe", AdminProbeView.as_view(), name="auth-admin-probe"),
]

from django.urls import path

from accounts.admin_views import (
    AdminAccessPermissionDetailView,
    AdminAccessPermissionListCreateView,
    AdminPolicyRuleDetailView,
    AdminPolicyRuleListCreateView,
    AdminRoleDetailView,
    AdminRoleListCreateView,
    AdminRolePermissionGrantView,
    AdminUserRoleGrantView,
)
from accounts.views import AdminProbeView, CsrfTokenView, LoginView, LogoutView, MeView, RegisterView


urlpatterns = [
    path("csrf", CsrfTokenView.as_view(), name="auth-csrf"),
    path("register", RegisterView.as_view(), name="auth-register"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
    path("me", MeView.as_view(), name="auth-me"),
    path("admin-probe", AdminProbeView.as_view(), name="auth-admin-probe"),
    path("admin/roles", AdminRoleListCreateView.as_view(), name="admin-roles"),
    path("admin/roles/<int:pk>", AdminRoleDetailView.as_view(), name="admin-role-detail"),
    path(
        "admin/access-permissions",
        AdminAccessPermissionListCreateView.as_view(),
        name="admin-access-permissions",
    ),
    path(
        "admin/access-permissions/<int:pk>",
        AdminAccessPermissionDetailView.as_view(),
        name="admin-access-permission-detail",
    ),
    path(
        "admin/roles/<int:role_id>/permissions",
        AdminRolePermissionGrantView.as_view(),
        name="admin-role-permission-grant",
    ),
    path(
        "admin/roles/<int:role_id>/permissions/<int:permission_id>",
        AdminRolePermissionGrantView.as_view(),
        name="admin-role-permission-revoke",
    ),
    path(
        "admin/users/<int:user_id>/roles",
        AdminUserRoleGrantView.as_view(),
        name="admin-user-role-grant",
    ),
    path(
        "admin/users/<int:user_id>/roles/<int:role_id>",
        AdminUserRoleGrantView.as_view(),
        name="admin-user-role-revoke",
    ),
    path(
        "admin/policy-rules",
        AdminPolicyRuleListCreateView.as_view(),
        name="admin-policy-rules",
    ),
    path(
        "admin/policy-rules/<int:pk>",
        AdminPolicyRuleDetailView.as_view(),
        name="admin-policy-rule-detail",
    ),
]

from django.urls import path

from accounts.mock_views import WidgetsListView

urlpatterns = [
    path("widgets", WidgetsListView.as_view(), name="mock-widgets-list"),
]

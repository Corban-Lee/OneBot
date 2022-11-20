"""Urls for the dashboard app."""

from . import views


# Urls for the dashboard app
# Format: (path, name, view function, )
urlpatterns = [
    ("/callback", "callback", views.callback),
    ("/", "index", views.index),
    ("/dashboard", "dashboard", views.dashboard),
    ("/my-servers", "my-servers", views.my_servers),
    ("/docs", "documentation", views.documentation),
    ("/commands", "command-list", views.command_list),
    ("/help", "help-page", views.help_page)
]

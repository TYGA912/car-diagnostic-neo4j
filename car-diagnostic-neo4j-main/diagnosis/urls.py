from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("mechanic/dashboard/", views.mechanic_dashboard, name="mechanic_dashboard"),
    path("mechanic/dashboard/", views.mechanic_dashboard, name="mechanic_dashboard"),
    path("mechanic/requests/<str:request_id>/<str:action>/", views.handle_request, name="handle_request"),
    path("mechanic/add-knowledge/", views.mechanic_problem_select, name="mechanic_problem_select"),
    path("mechanic/solutions/", views.mechanic_solutions, name="mechanic_solution_list"),
    path("cars/<str:car_model>/dashboard/", views.dashboard, name="dashboard"),
    path("cars/<str:car_model>/parts/", views.part_list, name="part_list"),
    path("cars/<str:car_model>/parts/<str:part_name>/problems/", views.problem_list, name="problem_list"),
    path("cars/<str:car_model>/parts/<str:part_name>/problems/<str:problem_description>/solutions/", views.solution_list, name="solution_list"),
    path("add_solution/<str:problem_description>/", views.add_solution, name="add_solution"),
    path("contact_mechanic/<str:mechanic_name>/", views.contact_mechanic, name="contact_mechanic"),

    # Admin Management URLs
    path("admin/users/", views.admin_users_list, name="admin_users_list"),
    path("admin/users/add/", views.admin_user_add, name="admin_user_add"),
    path("admin/users/edit/<str:user_id>/", views.admin_user_edit, name="admin_user_edit"),
    path("admin/users/delete/<str:user_id>/", views.admin_user_delete, name="admin_user_delete"),
    path("admin/data/", views.admin_problems_list, name="admin_problems_list"),
]

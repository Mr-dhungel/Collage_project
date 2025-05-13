from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Voter management URLs
    path('voters/', views.VoterListView.as_view(), name='voter_list'),
    path('voters/add/', views.VoterCreateView.as_view(), name='voter_create'),
    path('voters/<int:pk>/edit/', views.VoterUpdateView.as_view(), name='voter_update'),
    path('voters/<int:pk>/delete/', views.VoterDeleteView.as_view(), name='voter_delete'),

    # Admin management URLs
    path('admins/', views.AdminListView.as_view(), name='admin_list'),
    path('admins/add/', views.AdminCreateView.as_view(), name='admin_create'),
    path('admins/<int:pk>/edit/', views.AdminUpdateView.as_view(), name='admin_update'),
    path('admins/<int:pk>/delete/', views.AdminDeleteView.as_view(), name='admin_delete'),

    # Facial recognition URLs
    path('voters/<int:pk>/register-face/', views.register_voter_face, name='register_voter_face'),
    path('face-login/<int:user_id>/', views.face_login_view, name='face_login'),
    path('face-login/<int:user_id>/verify/', views.verify_voter_face, name='verify_voter_face'),
]

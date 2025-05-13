from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Voting URLs
    path('votings/', views.VotingListView.as_view(), name='voting_list'),
    path('votings/add/', views.VotingCreateView.as_view(), name='voting_create'),
    path('votings/<int:pk>/', views.VotingDetailView.as_view(), name='voting_detail'),
    path('votings/<int:pk>/edit/', views.VotingUpdateView.as_view(), name='voting_update'),
    path('votings/<int:pk>/delete/', views.VotingDeleteView.as_view(), name='voting_delete'),
    path('votings/<int:pk>/results/', views.VotingResultsView.as_view(), name='voting_results'),
    path('votings/<int:pk>/voters/', views.VotingVoterUpdateView.as_view(), name='voting_voters'),

    # Post URLs
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('votings/<int:voting_pk>/posts/add/', views.PostCreateView.as_view(), name='post_create'),
    path('posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),

    # Candidate URLs
    path('candidates/', views.CandidateListView.as_view(), name='candidate_list'),
    path('candidates/add/', views.CandidateCreateView.as_view(), name='candidate_create_standalone'),
    path('votings/<int:voting_pk>/candidates/add/', views.CandidateCreateView.as_view(), name='candidate_create'),
    path('posts/<int:post_pk>/candidates/add/', views.CandidateCreateView.as_view(), name='candidate_create_for_post'),
    path('votings/<int:voting_pk>/posts/<int:post_pk>/candidates/add/', views.CandidateCreateView.as_view(), name='candidate_create_for_voting_post'),
    path('candidates/<int:pk>/edit/', views.CandidateUpdateView.as_view(), name='candidate_update'),
    path('candidates/<int:pk>/delete/', views.CandidateDeleteView.as_view(), name='candidate_delete'),

    # Voting process URLs
    path('votings/<int:voting_pk>/vote/', views.cast_vote, name='cast_vote'),
    path('results/', views.public_results_list, name='public_results'),
]

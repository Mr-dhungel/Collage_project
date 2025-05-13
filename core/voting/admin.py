from django.contrib import admin
from .models import Voting, Candidate, Vote, VotingVoter

class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1

class VotingVoterInline(admin.TabularInline):
    model = VotingVoter
    extra = 1

@admin.register(Voting)
class VotingAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'is_active', 'has_ended')
    search_fields = ('title', 'description')
    list_filter = ('start_time', 'end_time')
    inlines = [CandidateInline, VotingVoterInline]

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'voting', 'vote_count')
    search_fields = ('name', 'voting__title')
    list_filter = ('voting',)

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate', 'voting', 'timestamp')
    search_fields = ('voter__username', 'candidate__name', 'voting__title')
    list_filter = ('voting', 'timestamp')

@admin.register(VotingVoter)
class VotingVoterAdmin(admin.ModelAdmin):
    list_display = ('voter', 'voting')
    search_fields = ('voter__username', 'voting__title')
    list_filter = ('voting',)

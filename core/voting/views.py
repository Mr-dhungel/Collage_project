from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Count

from .models import Voting, Candidate, Vote, VotingVoter
from .forms import VotingForm, CandidateForm, VoteForm, VotingVoterForm
from accounts.views import AdminRequiredMixin

@login_required
def home(request):
    if request.user.is_admin:
        return redirect('admin_dashboard')
    else:
        # Get active votings for this voter
        active_votings = Voting.objects.filter(
            voting_voters__voter=request.user,
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        )

        # Get upcoming votings for this voter
        upcoming_votings = Voting.objects.filter(
            voting_voters__voter=request.user,
            start_time__gt=timezone.now()
        )

        # Get votings this voter has already voted in
        voted_votings = Voting.objects.filter(
            votes__voter=request.user
        )

        context = {
            'active_votings': active_votings,
            'upcoming_votings': upcoming_votings,
            'voted_votings': voted_votings,
        }
        return render(request, 'voting/home.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_admin:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    active_votings = Voting.objects.filter(
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    )

    completed_votings = Voting.objects.filter(
        end_time__lt=timezone.now()
    )

    upcoming_votings = Voting.objects.filter(
        start_time__gt=timezone.now()
    )

    context = {
        'active_votings': active_votings,
        'completed_votings': completed_votings,
        'upcoming_votings': upcoming_votings,
    }
    return render(request, 'voting/admin_dashboard.html', context)

class VotingListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Voting
    template_name = 'voting/voting_list.html'
    context_object_name = 'votings'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Force evaluation of status methods for each voting
        for voting in context['votings']:
            voting.is_active_status = voting.is_active()
            voting.has_ended_status = voting.has_ended()
            voting.has_started_status = voting.has_started()
        return context

class VotingDetailView(LoginRequiredMixin, DetailView):
    model = Voting
    template_name = 'voting/voting_detail.html'
    context_object_name = 'voting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting = self.get_object()

        # Check if user has already voted
        has_voted = Vote.objects.filter(voter=self.request.user, voting=voting).exists()
        context['has_voted'] = has_voted

        # Only show results if voting has ended
        if voting.has_ended():
            results = Candidate.objects.filter(voting=voting).annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count')
            context['results'] = results

            # Find the winner(s)
            if results:
                max_votes = results.first().vote_count
                winners = results.filter(vote_count=max_votes)
                context['winners'] = winners

        # Add vote form if user hasn't voted and voting is active
        if not has_voted and voting.is_active():
            context['vote_form'] = VoteForm(voting=voting)

        return context

class VotingCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Voting
    form_class = VotingForm
    template_name = 'voting/voting_form.html'
    success_url = reverse_lazy('voting_list')

    def form_valid(self, form):
        messages.success(self.request, "Voting created successfully!")
        return super().form_valid(form)

class VotingUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Voting
    form_class = VotingForm
    template_name = 'voting/voting_form.html'
    success_url = reverse_lazy('voting_list')

    def form_valid(self, form):
        messages.success(self.request, "Voting updated successfully!")
        return super().form_valid(form)

class VotingDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Voting
    template_name = 'voting/voting_confirm_delete.html'
    success_url = reverse_lazy('voting_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Voting deleted successfully!")
        return super().delete(request, *args, **kwargs)

class CandidateListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Candidate
    template_name = 'voting/candidate_list.html'
    context_object_name = 'candidates'

    def get_queryset(self):
        return Candidate.objects.all().order_by('voting__title', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group candidates by voting
        candidates_by_voting = {}
        for candidate in context['candidates']:
            if candidate.voting not in candidates_by_voting:
                candidates_by_voting[candidate.voting] = []
            candidates_by_voting[candidate.voting].append(candidate)
        context['candidates_by_voting'] = candidates_by_voting
        return context

class CandidateCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'voting/candidate_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'voting_pk' in self.kwargs:
            kwargs['voting_pk'] = self.kwargs['voting_pk']
        return kwargs

    def get_success_url(self):
        if 'voting_pk' in self.kwargs:
            return reverse_lazy('voting_detail', kwargs={'pk': self.kwargs['voting_pk']})
        return reverse_lazy('candidate_list')

    def form_valid(self, form):
        if 'voting_pk' in self.kwargs:
            voting = get_object_or_404(Voting, pk=self.kwargs['voting_pk'])
            form.instance.voting = voting

        # Handle the uploaded photo
        if 'photo' in self.request.FILES:
            form.instance.photo = self.request.FILES['photo']

        messages.success(self.request, "Candidate added successfully!")
        return super().form_valid(form)

class CandidateUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'voting/candidate_form.html'

    def get_success_url(self):
        # Check if we came from the candidate list or a voting detail page
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'candidates' in referer:
            return reverse_lazy('candidate_list')
        return reverse_lazy('voting_detail', kwargs={'pk': self.object.voting.pk})

    def form_valid(self, form):
        # Handle the uploaded photo
        if 'photo' in self.request.FILES:
            form.instance.photo = self.request.FILES['photo']

        messages.success(self.request, "Candidate updated successfully!")
        return super().form_valid(form)

class CandidateDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Candidate
    template_name = 'voting/candidate_confirm_delete.html'

    def get_success_url(self):
        # Check if we came from the candidate list or a voting detail page
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'candidates' in referer:
            return reverse_lazy('candidate_list')
        return reverse_lazy('voting_detail', kwargs={'pk': self.object.voting.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Candidate deleted successfully!")
        return super().delete(request, *args, **kwargs)

class VotingVoterUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Voting
    form_class = VotingVoterForm
    template_name = 'voting/voting_voter_form.html'

    def get_success_url(self):
        return reverse_lazy('voting_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Voters updated successfully!")
        return super().form_valid(form)

@login_required
def cast_vote(request, voting_pk):
    voting = get_object_or_404(Voting, pk=voting_pk)

    # Check if user is assigned to this voting
    if not VotingVoter.objects.filter(voting=voting, voter=request.user).exists():
        messages.error(request, "You are not authorized to vote in this election.")
        return redirect('home')

    # Check if user has already voted
    if Vote.objects.filter(voter=request.user, voting=voting).exists():
        messages.error(request, "You have already voted in this election.")
        return redirect('voting_detail', pk=voting_pk)

    # Check if voting has ended
    if voting.has_ended():
        messages.error(request, "This voting has already ended.")
        return redirect('voting_detail', pk=voting_pk)

    # Check if voting has started - we'll allow voting as long as it has started
    if not voting.has_started():
        messages.error(request, "This voting has not started yet.")
        return redirect('voting_detail', pk=voting_pk)

    if request.method == 'POST':
        form = VoteForm(request.POST, voting=voting)
        if form.is_valid():
            vote = form.save(commit=False)
            vote.voter = request.user
            vote.voting = voting
            vote.save()
            messages.success(request, "Your vote has been recorded successfully!")
            return redirect('voting_detail', pk=voting_pk)
    else:
        form = VoteForm(voting=voting)

    return render(request, 'voting/cast_vote.html', {
        'form': form,
        'voting': voting
    })

class VotingResultsView(DetailView):
    model = Voting
    template_name = 'voting/voting_results.html'
    context_object_name = 'voting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting = self.get_object()

        # Only show results if voting has ended
        if voting.has_ended():
            results = Candidate.objects.filter(voting=voting).annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count')
            context['results'] = results

            # Find the winner(s)
            if results:
                max_votes = results.first().vote_count
                winners = results.filter(vote_count=max_votes)
                context['winners'] = winners
        else:
            messages.warning(self.request, "Results will be available after the voting ends.")

        return context

def public_results_list(request):
    """View for displaying a list of all completed votings with results"""
    # Get all votings
    all_votings = Voting.objects.all().order_by('-end_time')  # Most recently ended first

    # Filter to only include votings that have ended
    completed_votings = [voting for voting in all_votings if voting.has_ended()]

    context = {
        'completed_votings': completed_votings
    }
    return render(request, 'voting/public_results_list.html', context)




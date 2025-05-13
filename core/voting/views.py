from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Count
from django.db import connection

from .models import Voting, Candidate, Vote, VotingVoter, Post
from .forms import VotingForm, CandidateForm, VoteForm, VotingVoterForm, PostForm, MultiPostVoteForm, ExistingCandidateForm
from accounts.mixins import AdminRequiredMixin, VoterRequiredMixin

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

        # Get all posts for this voting
        posts = Post.objects.filter(voting=voting).order_by('order', 'title')
        context['posts'] = posts

        # Get candidates grouped by post
        candidates_by_post = {}
        for post in posts:
            candidates_by_post[post] = Candidate.objects.filter(voting=voting, post=post)

        # Also get candidates without posts
        candidates_without_post = Candidate.objects.filter(voting=voting, post__isnull=True)
        if candidates_without_post.exists():
            candidates_by_post['no_post'] = candidates_without_post

        context['candidates_by_post'] = candidates_by_post

        # Check if user has already voted for any post
        voted_posts = []
        for post in posts:
            if Vote.objects.filter(voter=self.request.user, voting=voting, post=post).exists():
                voted_posts.append(post)
        context['voted_posts'] = voted_posts

        # Check if user has voted for all posts
        context['has_voted_all'] = len(voted_posts) == len(posts)

        # Only show results if voting has ended
        if voting.has_ended():
            # Get results by post
            results_by_post = {}
            for post in posts:
                post_results = Candidate.objects.filter(voting=voting, post=post).annotate(
                    vote_count=Count('votes')
                ).order_by('-vote_count')

                results_by_post[post] = post_results

                # Find winners for each post
                if post_results:
                    max_votes = post_results.first().vote_count
                    winners = post_results.filter(vote_count=max_votes)
                    results_by_post[f"{post}_winners"] = winners

            context['results_by_post'] = results_by_post

        # Add multi-post vote form if user hasn't voted for all posts and voting is active
        if not context['has_voted_all'] and voting.is_active():
            context['multi_post_vote_form'] = MultiPostVoteForm(voting=voting)

        return context

class VotingCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Voting
    form_class = VotingForm
    template_name = 'voting/voting_form.html'
    success_url = reverse_lazy('voting_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage votings.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Voting created successfully!")
        return super().form_valid(form)

class VotingUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Voting
    form_class = VotingForm
    template_name = 'voting/voting_form.html'
    success_url = reverse_lazy('voting_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage votings.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Voting updated successfully!")
        return super().form_valid(form)

class VotingDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Voting
    template_name = 'voting/voting_confirm_delete.html'
    success_url = reverse_lazy('voting_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage votings.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Voting deleted successfully!")
        return super().delete(request, *args, **kwargs)

class CandidateListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'voting/candidate_list.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage candidates
        if request.user.is_admin and not request.user.can_manage_candidates and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage candidates.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Use raw SQL to avoid the post_id column issue
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, c.description, c.photo, c.voting_id, v.title as voting_title
                FROM voting_candidate c
                LEFT JOIN voting_voting v ON c.voting_id = v.id
                ORDER BY v.title, c.name
            """)
            columns = [col[0] for col in cursor.description]
            candidates = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Group candidates by voting
        candidates_by_voting = {}
        for candidate in candidates:
            voting_id = candidate['voting_id']
            if voting_id not in candidates_by_voting:
                candidates_by_voting[voting_id] = {
                    'title': candidate['voting_title'] or 'No Voting',
                    'candidates': []
                }
            candidates_by_voting[voting_id]['candidates'].append(candidate)

        return render(request, self.template_name, {
            'candidates_by_voting': candidates_by_voting
        })

class CandidateCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'voting/candidate_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage candidates
        if request.user.is_admin and not request.user.can_manage_candidates and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage candidates.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'voting_pk' in self.kwargs:
            kwargs['voting_pk'] = self.kwargs['voting_pk']
        if 'post_pk' in self.kwargs:
            kwargs['post_pk'] = self.kwargs['post_pk']
        return kwargs

    def get_success_url(self):
        # If we have a voting_pk, redirect to that voting's detail page
        if 'voting_pk' in self.kwargs:
            return reverse_lazy('voting_detail', kwargs={'pk': self.kwargs['voting_pk']})

        # If we have a post_pk but no voting_pk, get the voting from the post
        elif 'post_pk' in self.kwargs:
            post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
            if post.voting:
                return reverse_lazy('voting_detail', kwargs={'pk': post.voting.pk})

        # Default fallback
        return reverse_lazy('candidate_list')

    def form_valid(self, form):
        # Handle voting assignment
        if 'voting_pk' in self.kwargs:
            voting = get_object_or_404(Voting, pk=self.kwargs['voting_pk'])
            form.instance.voting = voting

        # Handle post assignment
        if 'post_pk' in self.kwargs:
            post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
            form.instance.post = post

            # If post is assigned but voting isn't, get the voting from the post
            if not form.instance.voting and post.voting:
                form.instance.voting = post.voting

        # Handle the uploaded photo
        if 'photo' in self.request.FILES:
            form.instance.photo = self.request.FILES['photo']

        messages.success(self.request, "Candidate added successfully!")
        return super().form_valid(form)

class CandidateUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Candidate
    form_class = CandidateForm
    template_name = 'voting/candidate_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage candidates
        if request.user.is_admin and not request.user.can_manage_candidates and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage candidates.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # Check if we came from the candidate list or a voting detail page
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'candidates' in referer or not self.object.voting:
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

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage candidates
        if request.user.is_admin and not request.user.can_manage_candidates and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage candidates.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # Check if we came from the candidate list or a voting detail page
        referer = self.request.META.get('HTTP_REFERER', '')
        if 'candidates' in referer or not self.object.voting:
            return reverse_lazy('candidate_list')
        return reverse_lazy('voting_detail', kwargs={'pk': self.object.voting.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Candidate deleted successfully!")
        return super().delete(request, *args, **kwargs)

class AddExistingCandidatesView(LoginRequiredMixin, AdminRequiredMixin, FormView):
    """
    View for adding existing candidates to a position.
    """
    template_name = 'voting/add_existing_candidates.html'
    form_class = ExistingCandidateForm

    def get_voting(self):
        """Get the voting object based on the URL parameter"""
        voting_pk = self.kwargs.get('voting_pk')
        return get_object_or_404(Voting, pk=voting_pk)

    def get_post(self):
        """Get the post object based on the URL parameter"""
        post_pk = self.kwargs.get('post_pk')
        return get_object_or_404(Post, pk=post_pk)

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage candidates
        if request.user.is_admin and not request.user.can_manage_candidates and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage candidates.")
            return redirect('admin_dashboard')

        # Check if voting and post exist
        try:
            self.get_voting()
            self.get_post()
        except:
            messages.error(request, "The specified voting or position does not exist.")
            return redirect('voting_list')

        # Call the parent class's dispatch method using the correct syntax
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['voting_pk'] = self.kwargs.get('voting_pk')
        kwargs['post_pk'] = self.kwargs.get('post_pk')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['voting'] = self.get_voting()
        context['post'] = self.get_post()

        # Check if there are any candidates available to add
        try:
            candidates_available = self.form_class(
                voting_pk=self.kwargs.get('voting_pk'),
                post_pk=self.kwargs.get('post_pk')
            ).fields['candidates'].queryset.exists()
        except Exception:
            candidates_available = False

        context['candidates_available'] = candidates_available
        return context

    def form_valid(self, form):
        selected_candidates = form.cleaned_data.get('candidates', [])
        voting = self.get_voting()
        post = self.get_post()

        if not selected_candidates:
            messages.info(self.request, "No candidates were selected.")
            return super().form_valid(form)

        # Assign the selected candidates to the post
        for candidate in selected_candidates:
            # If candidate has no voting, assign it to this voting
            if not candidate.voting:
                candidate.voting = voting

            # Assign the post
            candidate.post = post
            candidate.save()

        messages.success(
            self.request,
            f"{len(selected_candidates)} candidate{'s' if len(selected_candidates) > 1 else ''} added to {post.title}."
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('voting_detail', kwargs={'pk': self.kwargs.get('voting_pk')})

class VotingVoterUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Voting
    form_class = VotingVoterForm
    template_name = 'voting/voting_voter_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage votings.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

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

    # Check if voting has ended
    if voting.has_ended():
        messages.error(request, "This voting has already ended.")
        return redirect('voting_detail', pk=voting_pk)

    # Check if voting has started - we'll allow voting as long as it has started
    if not voting.has_started():
        messages.error(request, "This voting has not started yet.")
        return redirect('voting_detail', pk=voting_pk)

    # Get all posts for this voting
    posts = Post.objects.filter(voting=voting).order_by('order', 'title')

    # Check which posts the user has already voted for
    voted_posts = []
    for post in posts:
        if Vote.objects.filter(voter=request.user, voting=voting, post=post).exists():
            voted_posts.append(post)

    # If the user has voted for all posts, redirect to the voting detail page
    if len(voted_posts) == len(posts):
        messages.info(request, "You have already voted for all posts in this election.")
        return redirect('voting_detail', pk=voting_pk)

    if request.method == 'POST':
        form = MultiPostVoteForm(request.POST, voting=voting)
        if form.is_valid():
            votes_cast = 0

            # Process each post field in the form
            for field_name, candidate in form.cleaned_data.items():
                if candidate and field_name.startswith('post_'):
                    post_id = int(field_name.split('_')[1])
                    post = get_object_or_404(Post, pk=post_id)

                    # Check if user has already voted for this post
                    if Vote.objects.filter(voter=request.user, voting=voting, post=post).exists():
                        continue

                    # Create and save the vote
                    vote = Vote(
                        voter=request.user,
                        candidate=candidate,
                        voting=voting
                    )

                    # Only set post if it exists
                    if post:
                        vote.post = post
                    vote.save()
                    votes_cast += 1

            if votes_cast > 0:
                messages.success(request, f"Your vote{'s' if votes_cast > 1 else ''} for {votes_cast} position{'s' if votes_cast > 1 else ''} been recorded successfully!")
            else:
                messages.info(request, "No new votes were cast.")

            return redirect('voting_detail', pk=voting_pk)
    else:
        form = MultiPostVoteForm(voting=voting)

    return render(request, 'voting/cast_vote.html', {
        'form': form,
        'voting': voting,
        'posts': posts,
        'voted_posts': voted_posts
    })

class VotingResultsView(DetailView):
    model = Voting
    template_name = 'voting/voting_results.html'
    context_object_name = 'voting'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        voting = self.get_object()

        # Get all posts for this voting
        posts = Post.objects.filter(voting=voting).order_by('order', 'title')
        context['posts'] = posts

        # Only show results if voting has ended
        if voting.has_ended():
            # Get results by post
            results_by_post = {}
            for post in posts:
                post_results = Candidate.objects.filter(voting=voting, post=post).annotate(
                    vote_count=Count('votes')
                ).order_by('-vote_count')

                results_by_post[post] = post_results

                # Find winners for each post
                if post_results:
                    max_votes = post_results.first().vote_count
                    winners = post_results.filter(vote_count=max_votes)
                    results_by_post[f"{post}_winners"] = winners

            # Also get results for candidates without posts
            no_post_results = Candidate.objects.filter(voting=voting, post__isnull=True).annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count')

            if no_post_results.exists():
                results_by_post['no_post'] = no_post_results

                # Find winners for candidates without posts
                if no_post_results:
                    max_votes = no_post_results.first().vote_count
                    winners = no_post_results.filter(vote_count=max_votes)
                    results_by_post["no_post_winners"] = winners

            context['results_by_post'] = results_by_post

            # Also include overall results for backward compatibility
            all_results = Candidate.objects.filter(voting=voting).annotate(
                vote_count=Count('votes')
            ).order_by('-vote_count')
            context['results'] = all_results
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

class PostListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    Display a flat list of all positions with options to add candidates and edit.
    """
    model = Post
    template_name = 'voting/post_list.html'
    context_object_name = 'posts'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage positions.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Post.objects.all().select_related('voting').order_by('voting__title', 'order', 'title')

class PostCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'voting/post_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage positions.")
            return redirect('admin_dashboard')

        # If accessed directly without a voting_pk, redirect to voting list
        if 'voting_pk' not in self.kwargs:
            messages.info(request, "Positions can only be created within a voting. Please select a voting first.")
            return redirect('voting_list')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'voting_pk' in self.kwargs:
            kwargs['voting_pk'] = self.kwargs['voting_pk']
        return kwargs

    def get_success_url(self):
        # Redirect back to the voting detail page after creating a position
        return reverse_lazy('voting_detail', kwargs={'pk': self.kwargs['voting_pk']})

    def form_valid(self, form):
        voting = get_object_or_404(Voting, pk=self.kwargs['voting_pk'])
        form.instance.voting = voting

        messages.success(self.request, f"Position '{form.instance.title}' added successfully!")
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'voting/post_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage positions.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, f"Position '{self.object.title}' updated successfully.")
        return reverse_lazy('post_list')

    def form_valid(self, form):
        return super().form_valid(form)

class PostDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Post
    template_name = 'voting/post_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage votings
        if request.user.is_admin and not request.user.can_manage_votings and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage positions.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('post_list')

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        position_title = post.title

        # Delete the position
        response = super().delete(request, *args, **kwargs)

        # Store success message
        messages.success(self.request, f"Position '{position_title}' deleted successfully.")

        return response


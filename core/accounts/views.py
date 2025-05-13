from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import tempfile
import os
from .models import User
from .forms import (
    UserIdForm, PasswordForm, VoterCreationForm, VoterUpdateForm,
    AdminCreationForm, AdminUpdateForm
)
from facial_recognition import FacialRecognition

def login_view(request):
    user = None
    user_id_form = UserIdForm(request.POST or None)
    password_form = None
    show_password = False

    # Helper function to find user by ID (username or voter_id)
    def find_user_by_id(user_id):
        try:
            # First try to find by username (for admins)
            return User.objects.get(username=user_id)
        except User.DoesNotExist:
            try:
                # Then try to find by voter_id (for voters)
                return User.objects.get(voter_id=user_id)
            except User.DoesNotExist:
                return None

    if 'user_id' in request.POST:
        if user_id_form.is_valid():
            user_id = user_id_form.cleaned_data.get('user_id')
            user = find_user_by_id(user_id)

            if user:
                # For voters with facial recognition data, redirect to face login
                if user.is_voter and user.has_face_data:
                    request.session['voter_id_for_face_auth'] = user.voter_id
                    return redirect('face_login', user_id=user.id)

                # Otherwise show password form
                show_password = True
                password_form = PasswordForm()
                password_form.user = user
            else:
                messages.error(request, f"No user found with ID: {user_id}")

    elif 'password' in request.POST and 'user_id_value' in request.POST:
        user_id = request.POST.get('user_id_value')
        show_password = True

        user = find_user_by_id(user_id)
        if not user:
            messages.error(request, f"No user found with ID: {user_id}")
            return redirect('login')

        password_form = PasswordForm(data=request.POST)
        password_form.user = user
        if password_form.is_valid():
            password = password_form.cleaned_data.get('password')

            # Try to authenticate based on user type
            if user.is_admin:
                # For admin users, authenticate with username
                auth_user = authenticate(request, username=user.username, password=password)
            else:
                # For voters, authenticate with voter_id
                auth_user = authenticate(request, voter_id=user.voter_id, password=password)

            if auth_user is not None:
                login(request, auth_user)
                if auth_user.is_admin:
                    return redirect('admin_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, "Invalid password.")

    return render(request, 'accounts/login.html', {
        'user_id_form': user_id_form,
        'password_form': password_form,
        'show_password': show_password,
        'user': user,
        'user_id_value': request.POST.get('user_id') if 'user_id' in request.POST else ''
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class VoterListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/voter_list.html'
    context_object_name = 'voters'

    def get_queryset(self):
        return User.objects.filter(is_voter=True)

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage voters
        if request.user.is_admin and not request.user.can_manage_voters and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage voters.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

class VoterCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = VoterCreationForm
    template_name = 'accounts/voter_form.html'
    success_url = reverse_lazy('voter_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage voters
        if request.user.is_admin and not request.user.can_manage_voters and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage voters.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Save the form to create the user
        response = super().form_valid(form)

        # Check if facial recognition is enabled
        if form.cleaned_data.get('enable_facial_recognition'):
            # Redirect to facial recognition registration page
            messages.success(self.request, "Voter created successfully! Please register facial recognition data.")
            return redirect('register_voter_face', pk=self.object.pk)
        else:
            messages.success(self.request, "Voter created successfully!")
            return response

class VoterUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = VoterUpdateForm
    template_name = 'accounts/voter_form.html'
    success_url = reverse_lazy('voter_list')

    def get_queryset(self):
        return User.objects.filter(is_voter=True)

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage voters
        if request.user.is_admin and not request.user.can_manage_voters and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage voters.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Voter updated successfully!")
        return super().form_valid(form)

class VoterDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/voter_confirm_delete.html'
    success_url = reverse_lazy('voter_list')

    def get_queryset(self):
        return User.objects.filter(is_voter=True)

    def dispatch(self, request, *args, **kwargs):
        # Check if the admin has permission to manage voters
        if request.user.is_admin and not request.user.can_manage_voters and not request.user.is_superuser:
            messages.error(request, "You don't have permission to manage voters.")
            return redirect('admin_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        # Delete facial recognition data if it exists
        if user.has_face_data:
            try:
                face_recognizer = FacialRecognition()
                if user.voter_id in face_recognizer.face_db:
                    # Remove from database
                    db_path = face_recognizer.db_path
                    embedding_path = os.path.join(db_path, f"{user.voter_id}.npy")
                    if os.path.exists(embedding_path):
                        os.remove(embedding_path)
            except Exception as e:
                messages.warning(self.request, f"Could not delete facial recognition data: {str(e)}")

        messages.success(self.request, "Voter deleted successfully!")
        return super().delete(request, *args, **kwargs)

# Admin management views
class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Only superusers can manage admin accounts.")
        return redirect('admin_dashboard')

class AdminListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/admin_list.html'
    context_object_name = 'admins'

    def get_queryset(self):
        # Superusers can see all admins
        return User.objects.filter(is_admin=True)

class AdminCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = User
    form_class = AdminCreationForm
    template_name = 'accounts/admin_form.html'
    success_url = reverse_lazy('admin_list')

    def form_valid(self, form):
        messages.success(self.request, "Admin user created successfully!")
        return super().form_valid(form)

class AdminUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = AdminUpdateForm
    template_name = 'accounts/admin_form.html'
    success_url = reverse_lazy('admin_list')

    def get_queryset(self):
        return User.objects.filter(is_admin=True)

    def dispatch(self, request, *args, **kwargs):
        # First check if user is superuser (handled by the mixin)
        response = super().dispatch(request, *args, **kwargs)

        # If we got here, user is a superuser, now check if they're trying to edit themselves
        admin_user = self.get_object()

        # Prevent editing superuser status through the form
        if admin_user.pk == request.user.pk and 'is_superuser' in request.POST:
            messages.error(request, "You cannot modify your own superuser status.")
            return redirect('admin_list')

        return response

    def form_valid(self, form):
        messages.success(self.request, "Admin user updated successfully!")
        return super().form_valid(form)

class AdminDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/admin_confirm_delete.html'
    success_url = reverse_lazy('admin_list')

    def get_queryset(self):
        return User.objects.filter(is_admin=True)

    def dispatch(self, request, *args, **kwargs):
        # First check if user is superuser (handled by the mixin)
        response = super().dispatch(request, *args, **kwargs)

        # If we got here, user is a superuser, now check if they're trying to delete themselves
        admin_user = self.get_object()

        # Prevent deleting yourself
        if admin_user.pk == request.user.pk:
            messages.error(request, "You cannot delete your own admin account.")
            return redirect('admin_list')

        return response

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Admin user deleted successfully!")
        return super().delete(request, *args, **kwargs)

# Removed register_voter_face_view as it's now integrated into the voter edit page

@csrf_exempt
def register_voter_face(request, pk):
    """View and API endpoint for registering a voter's face"""
    if not request.user.is_authenticated or not request.user.is_admin:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    voter = get_object_or_404(User, pk=pk, is_voter=True)

    # Handle GET request - render the face registration template
    if request.method == 'GET':
        return render(request, 'accounts/face_registration.html', {
            'voter': voter
        })

    # Handle POST request - process facial recognition data
    elif request.method == 'POST':
        # Get the action from the request
        action = request.POST.get('action', 'register')

        # Initialize facial recognition
        try:
            face_recognizer = FacialRecognition(threshold=0.6)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f"Error initializing facial recognition: {str(e)}"
            })

        # Handle face validation
        if action == 'validate':
            # Get image data
            image_data = request.POST.get('image_data')
            if not image_data:
                return JsonResponse({'success': False, 'error': 'No image data provided'})

            # Remove data URL prefix
            if 'base64,' in image_data:
                image_data = image_data.split('base64,')[1]

            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data)

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(image_bytes)
                    temp_path = temp_file.name

                # Load image for face detection
                import cv2
                img = cv2.imread(temp_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Detect faces
                faces = face_recognizer.detect_face(img_rgb)

                # Clean up temp file
                os.unlink(temp_path)

                if not faces:
                    return JsonResponse({
                        'success': False,
                        'error': 'No face detected in the image. Please try again with better lighting and positioning.'
                    })

                # Get the largest face and its confidence
                largest_face = max(faces, key=lambda x: x['box'][2] * x['box'][3])
                confidence = largest_face.get('confidence', 0.0)

                return JsonResponse({
                    'success': True,
                    'face_count': len(faces),
                    'confidence': float(confidence)
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing image: {str(e)}'
                })

        # Handle face registration
        elif action == 'register':
            # Process each image
            image_count = 0
            successful_images = 0
            failed_images = 0
            errors = []

            for key in request.POST:
                if key.startswith('image_'):
                    image_count += 1
                    image_data = request.POST[key]

                    # Remove data URL prefix
                    if 'base64,' in image_data:
                        image_data = image_data.split('base64,')[1]

                    # Decode base64 image
                    try:
                        image_bytes = base64.b64decode(image_data)

                        # Save to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                            temp_file.write(image_bytes)
                            temp_path = temp_file.name

                        # Register face
                        success = face_recognizer.register_face(voter.voter_id, img_path=temp_path)

                        # Clean up temp file
                        os.unlink(temp_path)

                        if success:
                            successful_images += 1
                        else:
                            failed_images += 1
                            errors.append(f'No face detected in image {image_count}')

                    except Exception as e:
                        failed_images += 1
                        errors.append(f'Error processing image {image_count}: {str(e)}')

            # Check if we have enough successful images
            if successful_images == 0:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid face images were processed. Please try again.',
                    'details': errors
                })

            # Update user model
            voter.has_face_data = True
            voter.face_samples_count = successful_images
            voter.save()

            # Prepare response message
            message = f'Successfully registered {successful_images} face samples for {voter.first_name} {voter.last_name}'
            if failed_images > 0:
                message += f' ({failed_images} images failed)'

            return JsonResponse({
                'success': True,
                'message': message,
                'successful_images': successful_images,
                'failed_images': failed_images,
                'errors': errors if failed_images > 0 else []
            })

        # Handle clearing face data
        elif action == 'clear':
            try:
                # Check if user has face data
                if not voter.has_face_data:
                    return JsonResponse({
                        'success': False,
                        'error': 'This voter does not have any facial recognition data.'
                    })

                # Delete face embedding file
                db_path = face_recognizer.db_path
                embedding_path = os.path.join(db_path, f"{voter.voter_id}.npy")

                if os.path.exists(embedding_path):
                    os.remove(embedding_path)

                # Update user model
                voter.has_face_data = False
                voter.face_samples_count = 0
                voter.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Successfully cleared facial recognition data for {voter.first_name} {voter.last_name}'
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error clearing facial recognition data: {str(e)}'
                })

        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def face_login_view(request, user_id):
    """View for facial recognition login"""
    # Check if we have a voter ID in session
    voter_id = request.session.get('voter_id_for_face_auth')
    if not voter_id:
        messages.error(request, "Invalid login attempt.")
        return redirect('login')

    user = get_object_or_404(User, pk=user_id, voter_id=voter_id, is_voter=True, has_face_data=True)

    return render(request, 'accounts/face_login.html', {
        'user': user
    })

@csrf_exempt
def verify_voter_face(request, user_id):
    """API endpoint for verifying a voter's face"""
    # Check if we have a voter ID in session
    voter_id = request.session.get('voter_id_for_face_auth')
    if not voter_id:
        return JsonResponse({'success': False, 'error': 'Invalid login attempt'}, status=403)

    user = get_object_or_404(User, pk=user_id, voter_id=voter_id, is_voter=True, has_face_data=True)

    if request.method == 'POST':
        # Get the action from the request
        action = request.POST.get('action', 'verify')

        # Initialize facial recognition
        try:
            face_recognizer = FacialRecognition(threshold=0.6)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f"Error initializing facial recognition: {str(e)}"
            })

        # Get image data
        image_data = request.POST.get('image_data')
        if not image_data:
            return JsonResponse({'success': False, 'error': 'No image data provided'})

        # Remove data URL prefix
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]

        # Handle face validation
        if action == 'validate':
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data)

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(image_bytes)
                    temp_path = temp_file.name

                # Load image for face detection
                import cv2
                img = cv2.imread(temp_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Detect faces
                faces = face_recognizer.detect_face(img_rgb)

                # Clean up temp file
                os.unlink(temp_path)

                if not faces:
                    return JsonResponse({
                        'success': False,
                        'error': 'No face detected in the image. Please try again with better lighting and positioning.'
                    })

                # Get the largest face and its confidence
                largest_face = max(faces, key=lambda x: x['box'][2] * x['box'][3])
                confidence = largest_face.get('confidence', 0.0)

                return JsonResponse({
                    'success': True,
                    'face_count': len(faces),
                    'confidence': float(confidence)
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing image: {str(e)}'
                })

        # Handle face verification
        elif action == 'verify':
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(image_data)

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    temp_file.write(image_bytes)
                    temp_path = temp_file.name

                # First check if a face is detected
                import cv2
                img = cv2.imread(temp_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Detect faces
                faces = face_recognizer.detect_face(img_rgb)

                if not faces:
                    # Clean up temp file
                    os.unlink(temp_path)
                    return JsonResponse({
                        'success': False,
                        'error': 'No face detected in the image. Please try again with better lighting and positioning.'
                    })

                # Recognize face
                recognized_id, confidence = face_recognizer.recognize_face(img_path=temp_path)

                # Clean up temp file
                os.unlink(temp_path)

                # Check if recognized
                if recognized_id == user.voter_id:
                    # Import the USING_ADVANCED flag to check which implementation is being used
                    from facial_recognition import USING_ADVANCED

                    # Check confidence threshold based on which implementation is being used
                    if USING_ADVANCED:
                        # For advanced implementation, higher scores are better (0.0 to 1.0)
                        # A score of 0.94 (94%) is excellent
                        if confidence < 0.7:  # Threshold for advanced implementation
                            return JsonResponse({
                                'success': False,
                                'error': f'Low confidence match ({confidence:.1%}). Please try again with better lighting and positioning.',
                                'confidence': float(confidence)
                            })
                    else:
                        # For basic implementation, lower scores are better (0.0 to 1.0)
                        # But the confidence is returned as 1.0 - score, so higher is better
                        if confidence < 0.5:  # Threshold for basic implementation
                            return JsonResponse({
                                'success': False,
                                'error': f'Low confidence match ({confidence:.1%}). Please try again with better lighting and positioning.',
                                'confidence': float(confidence)
                            })

                    # Log the user in
                    user.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, user)

                    # Clear session data
                    if 'voter_id_for_face_auth' in request.session:
                        del request.session['voter_id_for_face_auth']

                    return JsonResponse({
                        'success': True,
                        'message': 'Identity verified successfully',
                        'confidence': float(confidence),
                        'redirect_url': reverse_lazy('home')
                    })
                else:
                    # Import the USING_ADVANCED flag to check which implementation is being used
                    from facial_recognition import USING_ADVANCED

                    # Check if it's a close match based on which implementation is being used
                    if USING_ADVANCED:
                        # For advanced implementation, higher scores are better
                        if confidence > 0.5:  # Higher threshold for "close match" with advanced implementation
                            error_message = f'Face verification failed with a close match ({confidence:.1%}). Please try again with better lighting and positioning.'
                        else:
                            error_message = 'Face verification failed. The face does not match our records.'
                    else:
                        # For basic implementation, confidence is returned as 1.0 - score, so higher is better
                        if confidence > 0.3:  # Threshold for basic implementation
                            error_message = f'Face verification failed with a close match ({confidence:.1%}). Please try again with better lighting and positioning.'
                        else:
                            error_message = 'Face verification failed. The face does not match our records.'

                    return JsonResponse({
                        'success': False,
                        'error': error_message,
                        'confidence': float(confidence)
                    })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing image: {str(e)}'
                })

        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

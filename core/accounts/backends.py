from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class VoterIdBackend(ModelBackend):
    def authenticate(self, request, voter_id=None, password=None, **kwargs):
        if voter_id is None:
            return None
        
        try:
            user = User.objects.get(voter_id=voter_id)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
        return None

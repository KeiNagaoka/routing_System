from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("name",)

class LoginFrom(AuthenticationForm):

    class Meta:
        model = User

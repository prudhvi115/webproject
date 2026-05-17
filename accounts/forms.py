from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default learning style and make email required
        self.fields['learning_style'].initial = 'visual'
        self.fields['learning_style'].required = True
        self.fields['email'].required = True
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'learning_style', 'interests', 'bio', 'avatar')
        widgets = {
            'learning_style': forms.RadioSelect(attrs={'class': 'radio-style'}),
        }

class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make learning style required
        self.fields['learning_style'].required = True
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'learning_style', 'interests', 'bio', 'avatar')
        widgets = {
            'learning_style': forms.RadioSelect(attrs={'class': 'radio-style'}),
        }

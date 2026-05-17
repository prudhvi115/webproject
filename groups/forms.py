from django import forms
from .models import StudyGroup

class StudyGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values if not editing existing group
        if not self.instance.pk:
            self.fields['preferred_learning_style'].initial = 'Any'
            self.fields['difficulty_level'].initial = 'Beginner'
        # Make fields required
        self.fields['preferred_learning_style'].required = True
        self.fields['difficulty_level'].required = True
    
    class Meta:
        model = StudyGroup
        fields = ['name', 'description', 'subject', 'preferred_learning_style', 'difficulty_level']
        widgets = {
            'preferred_learning_style': forms.RadioSelect(attrs={'class': 'radio-style'}),
            'difficulty_level': forms.RadioSelect(attrs={'class': 'radio-style'}),
        }

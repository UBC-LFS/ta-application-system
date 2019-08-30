from django import forms
from django.contrib.auth.models import User
from .models import *
from . import api
from datetime import datetime
import datetime as dt


DATE = datetime.now()


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['name']

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name']

class DegreeForm(forms.ModelForm):
    class Meta:
        model = Degree
        fields = ['name']

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name']

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name']

class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True})
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        labels = { 'email': 'Email', 'username': 'CWL' }
        help_texts = { 'username': None }
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
            'username': forms.TextInput(attrs={'required': True}),
        }

class ConfidentialityForm(forms.ModelForm):
    study_permit_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20))
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'sin', 'employee_number', 'study_permit', 'study_permit_expiry_date']
        widgets = {
            'user': forms.HiddenInput(),
            'sin': forms.FileInput(),
            'study_permit': forms.FileInput()
        }

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['user', 'file']
        widgets = {
            'user': forms.HiddenInput()
        }

class ProfileRoleForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Profile
        fields = ['user', 'roles']
        widgets = {
            'user': forms.HiddenInput()
        }


#checked
class ProfileForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    graduation_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20))
    )
    degrees = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Degree.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    trainings = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Training.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Profile
        fields = ['user', 'roles', 'qualifications','prior_employment', 'special_considerations',
                    'status', 'program', 'graduation_date', 'degrees', 'trainings',
                    'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
                    'ta_experience_details', 'preferred_name']
        widgets = {
            'user': forms.HiddenInput(),
            'qualifications': forms.Textarea(attrs={'rows':2}),
            'prior_employment': forms.Textarea(attrs={'rows':2}),
            'special_considerations': forms.Textarea(attrs={'rows':2}),
            'lfs_ta_training_details': forms.Textarea(attrs={'rows':2}),
            'ta_experience_details': forms.Textarea(attrs={'rows':2})
        }

    field_order = ['preferred_name', 'roles', 'qualifications','prior_employment', 'special_considerations',
                'status', 'program', 'graduation_date', 'degrees', 'trainings',
                'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
                'ta_experience_details']


#checked
class StudentProfileForm(forms.ModelForm):
    """ This is a model form for student profile """
    date = datetime.now()
    graduation_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(date.year, date.year + 20))
    )
    degrees = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Degree.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    trainings = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Training.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Profile
        fields = ['preferred_name', 'qualifications','prior_employment', 'special_considerations',
                    'status', 'program', 'graduation_date', 'degrees', 'trainings',
                    'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
                    'ta_experience_details']
        widgets = {
            'qualifications': forms.Textarea(attrs={'rows':2}),
            'prior_employment': forms.Textarea(attrs={'rows':2}),
            'special_considerations': forms.Textarea(attrs={'rows':2}),
            'lfs_ta_training_details': forms.Textarea(attrs={'rows':2}),
            'ta_experience_details': forms.Textarea(attrs={'rows':2})
        }

    field_order = ['preferred_name', 'qualifications','prior_employment', 'special_considerations',
                'status', 'program', 'graduation_date', 'degrees', 'trainings',
                'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
                'ta_experience_details']


    """
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super(StudentProfileForm, self).__init__(*args, **kwargs)
        print(self.initial)
        print(kwargs)
        print(self.instance)
        #if self.instance:
        #    print('instance', self.instance)
    """

class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['status', 'program']

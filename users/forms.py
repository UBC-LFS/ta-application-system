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
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }

class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }

class DegreeForm(forms.ModelForm):
    class Meta:
        model = Degree
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }

"""
class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'required': True}),
            'last_name': forms.TextInput(attrs={'required': True})
        }
"""

class UserForm(forms.ModelForm):
    ''' User model form '''
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

class UserCreateProfileForm(forms.ModelForm):
    ''' To check a profile while creating a user '''
    class Meta:
        model = Profile
        fields = ['preferred_name', 'ubc_number', 'roles']


class ConfidentialityCheckForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'is_international']
        widgets = {
            'user': forms.HiddenInput()
        }

class ConfidentialityNonInternationalForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'employee_number', 'sin']
        widgets = {
            'user': forms.HiddenInput()
        }

class ConfidentialityInternationalForm(forms.ModelForm):
    sin_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='SIN Expiry Date',
        help_text='Valid file formats: JPG, JPEG, PNG'
    )
    study_permit_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='Study Permit Expiry Date',
        help_text='Valid file formats: JPG, JPEG, PNG'
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
        widgets = {
            'user': forms.HiddenInput(),
            'sin': forms.FileInput(),
            'study_permit': forms.FileInput()
        }
        labels = {
            'employee_number': 'Employee Number',
            'sin': 'Social Insurance Number (SIN)',
            'study_permit': 'Study Permit'
        }


class ConfidentialityForm(forms.ModelForm):
    sin_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20))
    )
    study_permit_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20))
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'is_international','employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
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

class StudentProfileForm(forms.ModelForm):
    ''' This is a model form for student profile '''
    date = datetime.now()

    preferred_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={ 'class':'form-control' }),
        label='Preferred Name',
        help_text='The use of a Preferred Name is optional',
    )

    graduation_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(date.year, date.year + 20)),
        label='Anticipated Graduation'
    )
    degrees = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Degree.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Most Recent Degree',
        help_text='Please indicate your most recent completed or conferred degree (ex. BSc - Biochemistry - U of T, November 24, 2014)'
    )
    trainings = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Training.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        label='Training',
    )
    class Meta:
        model = Profile
        fields = [
            'preferred_name', 'qualifications','prior_employment', 'special_considerations',
            'status', 'program', 'program_others','graduation_date', 'degrees', 'trainings',
            'training_details', 'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
            'ta_experience_details'
        ]
        widgets = {
            'program_others': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'training_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'lfs_ta_training_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'qualifications': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'prior_employment': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'special_considerations': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'ta_experience_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' })
        }
        labels = {
            'program': 'Current Program',
            'program_others': 'Other Program',
            'training_details': 'Training Details',
            'lfs_ta_training': 'LFS TA Training',
            'lfs_ta_training_details': 'LFS TA Training Details',
            'ta_experience': 'Previous TA Experience',
            'ta_experience_details': 'Previous TA Experience Details',
            'qualifications': 'Explanation of Qualifications',
            'prior_employment': 'Information on Prior Employment (if any)',
            'special_considerations': 'Special Considerations'
        }
        help_texts = {
            'program': 'What program will you be registered in during the next Session?',
            'program_others': 'Please indicate your program if you select Others in the Current Program above.',
            'training_details': 'If you have completed TA and/or PBL training, please provide some details (name of workshop, dates of workshop, etc) in the text box.',
            'lfs_ta_training_details': 'Have you completed any LFS TA training sessions? If yes, please provide details (name of session/workshop, dates, etc).',
            'ta_experience_details': 'If yes, please list course name & session (example: FHN 350 002, 2010W Term 2)',
            'qualifications': 'List and give a 2-3 sentence justification of your qualifications for your top three preferred courses. If you list fewer than three, justfiy all of them. Qualifications might include coursework experience, TA expericne, work in the area, contact with the course\'s instructor, etc. List any special arrangements you have made with regard to TAing here.',
            'prior_employment': 'Please let any current or previous employment history you feel is relevant to the position you are applying for as a TA. Include company name, position, length of employment, supervisor\'s name and contact information (phone or email). Please indicate if you do not wish us to contact any employer for a reference.',
            'special_considerations': 'List any qualifications, experience, special considerations which may apply to this application. For example, you might list prior teaching experience, describe any special arrangements or requests for TAing with a particular instructor or for a particular course, or include a text copy of your current resume.'
        }

    field_order = [
        'preferred_name', 'status', 'program', 'program_others','graduation_date',
        'degrees', 'trainings', 'training_details',
        'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience','ta_experience_details',
        'qualifications','prior_employment', 'special_considerations'
    ]


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

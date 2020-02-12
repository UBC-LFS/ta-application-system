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


class UserForm(forms.ModelForm):
    ''' User model form '''
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        labels = { 'email': 'Email', 'username': 'CWL' }
        help_texts = {
            'first_name': 'Required',
            'last_name': 'Required',
            'email': 'Required',
            'username': 'Required'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'last_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'email': forms.EmailInput(attrs={ 'required': True, 'class': 'form-control' }),
            'username': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
        }

class UserProfileForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        help_text='Required'
    )
    class Meta:
        model = Profile
        fields = ['student_number', 'preferred_name', 'roles']
        labels = {
            'student_number': 'Student Number',
            'preferred_name': 'Preferred Name'
        }
        widgets = {
            'student_number': forms.TextInput(attrs={ 'class': 'form-control' }),
            'preferred_name': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'student_number': 'This field is optional and unique. Maximum length is 8.',
            'preferred_name': 'This field is optional. Maximum length is 256.'
        }


class UserProfileEditForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Profile
        fields = ['user', 'student_number', 'preferred_name', 'roles']
        labels = {
            'student_number': 'Student Number',
            'preferred_name': 'Preferred Name'
        }
        widgets = {
            'user': forms.HiddenInput(),
            'student_number': forms.TextInput(attrs={ 'class': 'form-control' }),
            'preferred_name': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'student_number': 'This field is optional and unique. Maximum length is 8.',
            'preferred_name': 'This field is optional. Maximum length is 256.'
        }

class StudentProfileForm(forms.ModelForm):
    ''' This is a model form for student profile '''
    date = datetime.now()

    preferred_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={ 'class':'form-control' }),
        label='Preferred Name',
        help_text='This field is optional. Maximum length is 256.'
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
        label='Most Recent Degrees',
        help_text='Please select your most recent degrees.'
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
            'status', 'program', 'program_others','graduation_date', 'degrees','degree_details',
            'trainings', 'training_details', 'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience', 'ta_experience_details'
        ]
        widgets = {
            'program_others': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'degree_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
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
            'degree_details': 'Degree Details',
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
            'degree_details': 'Please indicate your degree details: most recent completed or conferred or multiple same type degrees (ex. BSc - Biochemistry - U of T, November 24, 2014).',
            'training_details': 'If you have completed TA and/or PBL training, please provide some details (name of workshop, dates of workshop, etc) in the text box.',
            'lfs_ta_training_details': 'Have you completed any LFS TA training sessions? If yes, please provide details (name of session/workshop, dates, etc).',
            'ta_experience_details': 'If yes, please list course name & session (example: FHN 350 002, 2010W Term 2)',
            'qualifications': 'List and give a 2-3 sentence justification of your qualifications for your top three preferred courses. If you list fewer than three, justfiy all of them. Qualifications might include coursework experience, TA expericne, work in the area, contact with the course\'s instructor, etc. List any special arrangements you have made with regard to TAing here.',
            'prior_employment': 'Please let any current or previous employment history you feel is relevant to the position you are applying for as a TA. Include company name, position, length of employment, supervisor\'s name and contact information (phone or email). Please indicate if you do not wish us to contact any employer for a reference.',
            'special_considerations': 'List any qualifications, experience, special considerations which may apply to this application. For example, you might list prior teaching experience, describe any special arrangements or requests for TAing with a particular instructor or for a particular course, or include a text copy of your current resume.'
        }

    field_order = [
        'preferred_name', 'status', 'program', 'program_others','graduation_date',
        'degrees','degree_details', 'trainings', 'training_details',
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


class ConfidentialityCheckForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'nationality']
        widgets = {
            'user': forms.HiddenInput()
        }

class ConfidentialityDomesticForm(forms.ModelForm):
    nationality = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=Confidentiality.NATIONALITY_CHOICES,
        label='Am I a domestic or international student?',
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'nationality', 'employee_number', 'sin', 'personal_data_form']
        widgets = {
            'user': forms.HiddenInput(),
            'sin': forms.FileInput(),
            'personal_data_form': forms.FileInput()
        }
        labels = {
            'employee_number': 'Employee Number',
            'sin': 'Social Insurance Number (SIN)',
            'personal_data_form': 'Personal Data Form'
        }
        help_texts = {
            'employee_number': 'This field is optional and unique. Only 7-digit numerical value allowed.',
            'sin': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.',
            'personal_data_form': 'Valid file formats: PDF, DOC, DOCX. A filename has at most 256 characters.'
        }


class ConfidentialityInternationalForm(forms.ModelForm):
    nationality = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=Confidentiality.NATIONALITY_CHOICES,
        label='Am I a domestic or international student?',
    )
    sin_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='SIN Expiry Date'
    )
    study_permit_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='Study Permit Expiry Date'
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'nationality', 'employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date', 'personal_data_form']
        widgets = {
            'user': forms.HiddenInput(),
            'sin': forms.FileInput(),
            'study_permit': forms.FileInput(),
            'personal_data_form': forms.FileInput()
        }
        labels = {
            'employee_number': 'Employee Number',
            'sin': 'Social Insurance Number (SIN)',
            'study_permit': 'Study Permit',
            'personal_data_form': 'Personal Data Form'
        }
        help_texts = {
            'employee_number': 'This field is optional and unique. Only 7-digit numerical value allowed.',
            'sin': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.',
            'study_permit': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.',
            'personal_data_form': 'Valid file formats: PDF, DOC, DOCX. A filename has at most 256 characters.'
        }


class ConfidentialityForm(forms.ModelForm):
    nationality = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=Confidentiality.NATIONALITY_CHOICES,
        label='Am I a domestic or international student?',
    )
    sin_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='SIN Expiry Date'
    )
    study_permit_expiry_date = forms.DateField(
        required=False,
        widget=forms.SelectDateWidget(years=range(DATE.year, DATE.year + 20)),
        label='Study Permit Expiry Date'
    )
    class Meta:
        model = Confidentiality
        fields = ['user', 'nationality', 'employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date', 'personal_data_form']
        widgets = {
            'user': forms.HiddenInput(),
            'employee_number': forms.TextInput( attrs={ 'class': 'form-control' } ),
            'sin': forms.FileInput(),
            'study_permit': forms.FileInput()
        }
        labels = {
            'employee_number': 'Employee Number',
            'sin': 'Social Insurance Number (SIN)',
            'study_permit': 'Study Permit',
            'personal_data_form': 'Personal Data Form'
        }
        help_texts = {
            'employee_number': 'This field is optional and unique. Only 7-digit numerical value allowed.',
            'sin': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.',
            'study_permit': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.',
            'personal_data_form': 'Valid file formats: PDF, DOC, DOCX. A filename has at most 256 characters.'
        }
        field_order = ['user', 'nationality', 'employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date', 'personal_data_form']


class ResumeForm(forms.ModelForm):
    ''' '''
    class Meta:
        model = Resume
        fields = ['user', 'uploaded']
        labels = {
            'uploaded': ''
        }
        widgets = {
            'user': forms.HiddenInput()
        }

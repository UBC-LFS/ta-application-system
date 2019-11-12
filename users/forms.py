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
        help_texts = {
            'student_number': 'The use of a Student Number is optional',
            'preferred_name': 'The use of a Preferred Name is optional',
        }
        widgets = {
            'student_number': forms.TextInput(attrs={ 'class': 'form-control' }),
            'preferred_name': forms.TextInput(attrs={ 'class': 'form-control' })
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
        help_texts = {
            'student_number': 'The use of a Student Number is optional',
            'preferred_name': 'The use of a Preferred Name is optional',
        }
        widgets = {
            'user': forms.HiddenInput(),
            'student_number': forms.TextInput(attrs={ 'class': 'form-control' }),
            'preferred_name': forms.TextInput(attrs={ 'class': 'form-control' })
        }


"""
class UserCreateProfileForm(forms.ModelForm):
    ''' To check a profile while creating a user '''
    class Meta:
        model = Profile
        fields = ['preferred_name', 'student_number', 'roles']
"""

"""
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
"""




class StudentProfileForm(forms.ModelForm):
    ''' This is a model form for student profile '''
    date = datetime.now()

    student_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={ 'class':'form-control' }),
        label='Student Number'
    )

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
            'student_number', 'preferred_name', 'qualifications','prior_employment', 'special_considerations',
            'status', 'program', 'program_others','graduation_date', 'degrees', 'degree_details', 'trainings',
            'training_details', 'lfs_ta_training', 'lfs_ta_training_details', 'ta_experience',
            'ta_experience_details'
        ]
        widgets = {
            #'status': forms.Select(attrs={ 'class': 'form-control' }),
            #'program': forms.Select(attrs={ 'class': 'form-control' }),
            'program_others': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            #'graduation_date': forms.SelectDateWidget(attrs={ 'class': 'form-control' }),
            'degree_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'training_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            #'lfs_ta_training': forms.Select(attrs={ 'class': 'form-control' }),
            'lfs_ta_training_details': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'qualifications': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'prior_employment': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            'special_considerations': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' }),
            #'ta_experience': forms.Select(attrs={ 'class': 'form-control' }),
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
            'degree_details': 'Please indicate your most recent completed or conferred degrees (ex. BSc - Biochemistry - U of T, November 24, 2014)',
            'training_details': 'If you have completed TA and/or PBL training, please provide some details (name of workshop, dates of workshop, etc) in the text box.',
            'lfs_ta_training_details': 'Have you completed any LFS TA training sessions? If yes, please provide details (name of session/workshop, dates, etc).',
            'ta_experience_details': 'If yes, please list course name & session (example: FHN 350 002, 2010W Term 2)',
            'qualifications': 'List and give a 2-3 sentence justification of your qualifications for your top three preferred courses. If you list fewer than three, justfiy all of them. Qualifications might include coursework experience, TA expericne, work in the area, contact with the course\'s instructor, etc. List any special arrangements you have made with regard to TAing here.',
            'prior_employment': 'Please let any current or previous employment history you feel is relevant to the position you are applying for as a TA. Include company name, position, length of employment, supervisor\'s name and contact information (phone or email). Please indicate if you do not wish us to contact any employer for a reference.',
            'special_considerations': 'List any qualifications, experience, special considerations which may apply to this application. For example, you might list prior teaching experience, describe any special arrangements or requests for TAing with a particular instructor or for a particular course, or include a text copy of your current resume.'
        }

    field_order = [
        'student_number', 'preferred_name', 'status', 'program', 'program_others','graduation_date',
        'degrees', 'degree_details', 'trainings', 'training_details',
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
        fields = ['user', 'is_international']
        widgets = {
            'user': forms.HiddenInput()
        }

class ConfidentialityNonInternationalForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'employee_number', 'sin']
        widgets = {
            'user': forms.HiddenInput(),
            'sin': forms.FileInput()
        }
        labels = {
            'sin': 'Social Insurance Number (SIN)'
        }
        help_texts = {
            'sin': 'Valid file formats: JPG, JPEG, PNG'
        }


class ConfidentialityInternationalForm(forms.ModelForm):
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
        help_texts = {
            'sin': 'Valid file formats: JPG, JPEG, PNG',
            'study_permit': 'Valid file formats: JPG, JPEG, PNG'
        }


class ConfidentialityForm(forms.ModelForm):
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
        fields = ['user', 'is_international', 'employee_number', 'sin', 'sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
        widgets = {
            'user': forms.HiddenInput(),
            #'is_international': forms.Select( attrs={ 'class': 'form-control' } ),
            'employee_number': forms.TextInput( attrs={ 'class': 'form-control' } ),
            'sin': forms.FileInput(),
            'study_permit': forms.FileInput()
        }
        labels = {
            'is_international': 'Are you an International Student?',
            'employee_number': 'Employee Number',
            'sin': 'Social Insurance Number (SIN)',
            'study_permit': 'Study Permit'
        }
        help_texts = {
            'sin': 'Valid file formats: JPG, JPEG, PNG',
            'study_permit': 'Valid file formats: JPG, JPEG, PNG'
        }


class AdminDocumentsForm(forms.ModelForm):
    ''' '''
    class Meta:
        model = Confidentiality
        fields = ['user', 'is_international', 'employee_number', 'pin', 'tasm', 'eform', 'speed_chart','union_correspondence', 'compression_agreement', 'processing_note']
        labels = {
            'is_international': 'International Student',
            'employee_number': 'Employee Number',
            'pin': 'PIN',
            'tasm': 'TASM',
            'eform': 'eForm',
            'speed_chart': 'Speed Chart',
            'union_correspondence': 'Union and Other Correspondence',
            'compression_agreement': 'Compression Agreement',
            'processing_note': 'Processing Note'
        }
        widgets = {
            'user': forms.HiddenInput(),
            'employee_number': forms.TextInput(attrs={ 'class':'form-control' }),
            'pin': forms.TextInput(attrs={ 'class':'form-control' }),
            'eform': forms.TextInput(attrs={ 'class':'form-control' }),
            'speed_chart': forms.TextInput(attrs={ 'class':'form-control' }),
            'union_correspondence': forms.FileInput(),
            'compression_agreement': forms.FileInput(),
            'processing_note': forms.Textarea(attrs={ 'class':'form-control', 'rows': 2 }),
        }
        help_texts = {
            'is_international': 'Optional',
            'employee_number': 'Optional. Maximum 7 digits long',
            'pin': 'Optional. Maximum 4 digits long',
            'tasm': 'Optional',
            'eform': 'Optional. Maximum 6 digits long',
            'speed_chart': 'Optional',
            'union_correspondence': 'Optional. Valid file format: PDF only',
            'compression_agreement': 'Optional. Valid file format: PDF only',
            'processing_note': 'Optional'
        }


class ResumeForm(forms.ModelForm):
    ''' '''
    class Meta:
        model = Resume
        fields = ['user', 'uploaded']
        widgets = {
            'user': forms.HiddenInput()
        }



"""
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
"""

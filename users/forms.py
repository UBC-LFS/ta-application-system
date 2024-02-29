from django import forms
from django.contrib.auth.models import User
from .models import *
from datetime import datetime
from django_summernote.widgets import SummernoteWidget


DATE = datetime.now()

required_error = '<strong>{0}</strong>: This field is required.'
invalid_numeric_error = '<strong>{0}</strong>: Only positive numbers allowed.'


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


class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
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


class TrainingForm(forms.ModelForm):
    class Meta:
        model = Training
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={ 'class':'form-control' })
        }


class UserForm(forms.ModelForm):
    ''' User model form '''
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'is_superuser']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email',
            'username': 'CWL'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'last_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'email': forms.EmailInput(attrs={ 'required': True, 'class': 'form-control' }),
            'username': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' })
        }
        help_texts = {
            'first_name': 'Maximum length is 150 characters.',
            'last_name': 'Maximum length is 150 characters.',
            'email': 'Maximum length is 254 characters.',
            'username': 'Maximum length is 150 characters.',
            'is_superuser': "This field is necessary for Masquerade. If an user's role is an administrator or super-administrator, please select this field."
        }


class UserInstructorForm(forms.ModelForm):
    ''' User model form '''
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'last_name': forms.TextInput(attrs={ 'required': True, 'class': 'form-control' }),
            'email': forms.EmailInput(attrs={ 'required': True, 'class': 'form-control' })
        }
        help_texts = {
            'first_name': 'Maximum length is 150 characters.',
            'last_name': 'Maximum length is 150 characters.',
            'email': 'Maximum length is 254 characters.'
        }


class UserProfileForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
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
            'student_number': 'This field is optional. Must be numeric and 8 digits in length.',
            'preferred_name': 'This field is optional. Maximum length is 256 characters.'
        }


class UserProfileEditForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Profile
        fields = ['user', 'student_number', 'preferred_name', 'roles', 'is_trimmed']
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
            'student_number': 'This field is optional. Must be numeric and 8 digits in length.',
            'preferred_name': 'This field is optional. Maximum length is 256 characters.',
            'is_trimmed': "This field is False by default. It would be True if administrators destroy the contents of users who haven't logged in for 3 years."
        }


class StudentProfileGeneralForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'preferred_name', 'status', 'student_year', 'has_graduated', 'graduation_date', 'faculty', 'program', 'program_others',
            'degrees', 'degree_details', 'trainings', 'training_details', 'lfs_ta_training', 'lfs_ta_training_details'
        ]
        widgets = {
            'preferred_name': forms.TextInput(attrs={ 'class':'form-control' }),
            'status': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'student_year': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'has_graduated': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'graduation_date': forms.widgets.DateInput(attrs={ 'type': 'date', 'class': 'form-control', 'style': 'width:auto' }),
            'faculty': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'program': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'program_others': SummernoteWidget(),
            'degrees': forms.CheckboxSelectMultiple(),
            'degree_details': SummernoteWidget(),
            'trainings': forms.CheckboxSelectMultiple(),
            'training_details': SummernoteWidget(),
            'lfs_ta_training': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
            'lfs_ta_training_details': SummernoteWidget()
        }
        labels = {
            'preferred_name': 'Preferred Name',
            'student_year': 'Student Year',
            'has_graduated': 'Have you graduated?',
            'graduation_date': '(Anticipated) Graduation Date',
            'program': 'Current Program',
            'program_others': 'Other Program',
            'degrees': 'Most Recent Completed Degrees',
            'degree_details': 'Degree Details',
            'training_details': 'Training Details',
            'lfs_ta_training': 'LFS TA Training',
            'lfs_ta_training_details': 'LFS TA Training Details'
        }
        help_texts = {
            'preferred_name': 'This field is optional. Maximum length is 256 characters.',
            'student_year': 'What year of your UBC degree program are you in?',
            'program': 'What program will you be registered in during the next Session?',
            'graduation_date': 'Format: Year-Month-Day',
            'program_others': 'Please indicate the name of your program if you select "Other" in Current Program, above.',
            'degrees': 'Please select your most recent completed degrees.',
            'degree_details': 'Please indicate your degree details: most recent completed or conferred degree (e.g., BSc - Biochemistry - U of T, November 24, 2014).',
            'trainings': 'I acknowledge that I have completed or will be completing these training requirements as listed below prior to the start date of any TA appointment I may receive. (You must check all fields to proceed).',
            'training_details': 'If you have completed TA and/or PBL training, please provide some details (name of workshop, dates of workshop, etc) in the text box.',
            'lfs_ta_training_details': 'Have you completed any LFS TA training sessions? If yes, please provide details (name of session/workshop, dates, etc).'
        }
        error_messages = {
            'status': {
                'required': required_error.format('Status')
            },
            'student_year': {
                'required': required_error.format('Student Year')
            },
            'has_graduated': {
                'required': required_error.format('Have you graduated?')
            },
            'graduation_date': {
                'required': required_error.format('(Anticipated) Graduation Date')
            },
            'faculty': {
                'required': required_error.format('Faculty')
            },
            'program': {
                'required': required_error.format('Current Program')
            },
            'degrees': {
                'required': required_error.format('Most Recent Completed Degrees')
            },
            'degree_details': {
                'required': required_error.format('Degree Details')
            },
            'trainings': {
                'required': required_error.format('Trainings')
            },
            'training_details': {
                'required': required_error.format('Training Details')
            },
            'lfs_ta_training': {
                'required': required_error.format('LFS TA Training')
            },
            'lfs_ta_training_details': {
                'required': required_error.format('LFS TA Training Details')
            }
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].required = True
        self.fields['student_year'].required = True
        self.fields['has_graduated'].required = True
        self.fields['graduation_date'].required = True
        self.fields['faculty'].required = True
        self.fields['program'].required = True
        self.fields['degrees'].required = False
        self.fields['degree_details'].required = True
        self.fields['trainings'].required = False
        self.fields['training_details'].required = True
        self.fields['lfs_ta_training'].required = True
        self.fields['lfs_ta_training_details'].required = True

        self.fields['trainings'].queryset = Training.objects.filter(is_active=True)
    
    field_order = [
        'preferred_name', 'status', 'student_year', 'has_graduated', 'graduation_date', 'faculty', 'program', 'program_others',
        'degrees', 'degree_details', 'trainings', 'training_details', 'lfs_ta_training', 'lfs_ta_training_details'
    ]

student_profile_ta_fields = ['ta_experience', 'ta_experience_details', 'qualifications', 'qualifications', 'prior_employment', 'special_considerations']

student_profile_ta_widgets = {
    'ta_experience': forms.Select(attrs={ 'class': 'form-control', 'style': 'width:auto' }),
    'ta_experience_details': SummernoteWidget(),
    'qualifications': SummernoteWidget(),
    'prior_employment': SummernoteWidget(),
    'special_considerations': SummernoteWidget(),
}

student_profile_ta_labels = {
    'ta_experience': 'Previous TA Experience',
    'ta_experience_details': 'Previous TA Experience Details',
    'qualifications': 'Explanation of Qualifications',
    'prior_employment': 'Information on Prior Employment (if any)',
    'special_considerations': 'Special Considerations'
}

student_profile_ta_help_texts = {
    'ta_experience_details': 'If yes, please list course name, session and total hours worked in each course (example: FNH 350 002, 2010W Term 2, 120h)',
    'qualifications': "List and give a 2-3 sentence description of your qualifications for your top three preferred courses. If you list fewer than three courses, describe qualifications for all of them. Qualifications might include coursework experience, TA experience, work in the area, contact with the course's instructor, etc. List any special arrangements you have made with regard to TAing here.",
    'prior_employment': 'This is optional. Please let any current or previous employment history you feel is relevant to the position you are applying for as a TA. Include company name, position, length of employment, supervisor\'s name and contact information (phone or email). Please indicate if you do not wish us to contact any employer for a reference.',
    'special_considerations': 'This is optional. List any qualifications, experience, special considerations which may apply to this application. For example, you might list prior teaching experience, describe any special arrangements or requests for TAing with a particular instructor or for a particular course, or include a text copy of your current resume.'
}

ta_total_widgets = {
    'total_academic_years': forms.TextInput(attrs={ 'class':'form-control' }),
    'total_terms': forms.TextInput(attrs={ 'class':'form-control' }),
    'total_ta_hours': forms.TextInput(attrs={ 'class':'form-control' })
}

ta_total_labels = {
    'total_academic_years': 'Total number of academic years',
    'total_terms': 'Total number of terms',
    'total_ta_hours': 'Total number of GTA hours'
}

ta_total_ta_hours = {
    'total_academic_years': 'GTA only. Only positive numbers allowed.',
    'total_terms': 'GTA only. Only positive numbers allowed.',
    'total_ta_hours': 'GTA only. Only positive numbers allowed.'
}

ta_error_messages = {
    'ta_experience': {
        'required': required_error.format('Previous TA Experience')
    },
    'ta_experience_details': {
        'required': required_error.format('Previous TA Experience Details')
    },
    'qualifications': {
        'required': required_error.format('Explanation of Qualifications')
    }
}

class StudentProfileGraduateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['total_academic_years', 'total_terms', 'total_ta_hours'] + student_profile_ta_fields
        widgets = {**ta_total_widgets, **student_profile_ta_widgets}
        labels = {**ta_total_labels, **student_profile_ta_labels}
        help_texts = {**ta_total_ta_hours, **student_profile_ta_help_texts}
        error_messages = {
            'total_academic_years': {
                'required': required_error.format('Total number of academic years'),
                'invalid': invalid_numeric_error.format('Total number of academic years')
            },
            'total_terms': {
                'required': required_error.format('Total number of terms'),
                'invalid': invalid_numeric_error.format('Total number of terms')
            },
            'total_ta_hours': {
                'required': required_error.format('Total number of TA hours'),
                'invalid': invalid_numeric_error.format('Total number of TA hours')
            },
            **ta_error_messages
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total_academic_years'].required = True
        self.fields['total_terms'].required = True
        self.fields['total_ta_hours'].required = True
        self.fields['ta_experience'].required = True
        self.fields['ta_experience_details'].required = True
        self.fields['qualifications'].required = True


class StudentProfileUndergraduateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = student_profile_ta_fields
        widgets = student_profile_ta_widgets
        labels = student_profile_ta_labels
        help_texts = student_profile_ta_help_texts
        error_messages = ta_error_messages
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ta_experience'].required = True
        self.fields['ta_experience_details'].required = True
        self.fields['qualifications'].required = True


class InstructorProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['status', 'program']


class AlertForm(forms.ModelForm):
    ''' Students see an alert message in March and April '''
    class Meta:
        model = Alert
        fields = ['student', 'has_read']


class AlertEmailForm(forms.ModelForm):
    ''' Instructors send an alert email to students '''
    class Meta:
        model = AlertEmail
        fields = ['year', 'term', 'job_code', 'job_number', 'job_section', 'instructor', 'sender', 'receiver_name', 'receiver_email', 'title', 'message']


class ConfidentialityCheckForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'nationality']
        widgets = {
            'user': forms.HiddenInput()
        }


class EmployeeNumberForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['is_new_employee', 'employee_number']
        widgets = {
            'employee_number': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        labels = {
            'is_new_employee': 'I am a new employee',
            'employee_number': 'Employee Number'
        }
        help_texts = {
            'is_new_employee': "You are a new UBC employee if you have never had a UBC Employee Number or been paid by UBC.",
            'employee_number': 'Enter your UBC Employee ID number here, if you have one. Must be numeric and 7 digits in length.'
        }


class EmployeeNumberEditForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = ['user', 'is_new_employee', 'employee_number']
        widgets = {
            'user': forms.HiddenInput(),
            'employee_number': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        labels = {
            'is_new_employee': 'I am a new employee',
            'employee_number': 'Employee Number'
        }
        help_texts = {
            'is_new_employee': "You are a new UBC employee if you have never had a UBC Employee Number or been paid by UBC. ",
            'employee_number': 'Enter your UBC Employee ID number here, if you have one. Must be numeric and 7 digits in length.'
        }



confidentiality_fields = ['user', 'nationality', 'date_of_birth', 'is_new_employee', 'employee_number', 'sin']

confidentiality_widgets = {
    'user': forms.HiddenInput(),
    'nationality': forms.RadioSelect(),
    'date_of_birth': forms.widgets.DateInput(attrs={ 'type': 'date', 'class': 'form-control', 'style': 'width:auto' }),
    'employee_number': forms.TextInput(attrs={ 'class':'form-control' }),
    'sin': forms.FileInput()
}

confidentiality_labels = {
    'nationality': 'Am I a domestic or international student?', 
    'date_of_birth': 'Date of Birth:',
    'is_new_employee': 'I am a new employee:',
    'employee_number': 'Employee Number:',
    'sin': 'Social Insurance Number (SIN):'
}

confidentiality_help_texts = {
    'is_new_employee': "You are a new UBC employee if you have never had a UBC Employee Number or been paid by UBC. ",
    'employee_number': 'Enter your UBC Employee ID number here, if you have one. Must be numeric and 7 digits in length.',
    'sin': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.'
}

confidentiality_field_order = ['user', 'nationality', 'date_of_birth', 'is_new_employee', 'employee_number', 'sin']

international_widgets = {
    'sin_expiry_date': forms.widgets.DateInput(attrs={ 'type': 'date', 'class': 'form-control', 'style': 'width:auto' }),
    'study_permit': forms.FileInput(),
    'study_permit_expiry_date': forms.widgets.DateInput(attrs={ 'type': 'date', 'class': 'form-control', 'style': 'width:auto' })
}

international_labels = {
    'sin_expiry_date': 'SIN Expiry Date:',
    'study_permit': 'Study Permit:',
    'study_permit_expiry_date': 'Study Permit Expiry Date:'
}

international_help_texts = {
    'study_permit': 'Valid file formats: JPG, JPEG, PNG. A filename has at most 256 characters.'
}

class ConfidentialityDomesticForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = confidentiality_fields
        widgets = confidentiality_widgets
        labels = confidentiality_labels
        help_texts = confidentiality_help_texts

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nationality'].choices = Confidentiality.NATIONALITY_CHOICES

    field_order = confidentiality_field_order

    
class ConfidentialityInternationalForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = confidentiality_fields + ['sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
        widgets = {**confidentiality_widgets, **international_widgets}
        labels = {**confidentiality_labels, **international_labels}
        help_texts = {**confidentiality_help_texts, **international_help_texts}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nationality'].choices = Confidentiality.NATIONALITY_CHOICES

    field_order = confidentiality_field_order + ['sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
    

class ConfidentialityForm(forms.ModelForm):
    class Meta:
        model = Confidentiality
        fields = confidentiality_fields + ['sin_expiry_date', 'study_permit', 'study_permit_expiry_date']
        widgets = {**confidentiality_widgets, **international_widgets}
        labels = {**confidentiality_labels, **international_labels}
        help_texts = {**confidentiality_help_texts, **international_help_texts}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nationality'].choices = Confidentiality.NATIONALITY_CHOICES
    
    field_order = confidentiality_field_order + ['sin_expiry_date', 'study_permit', 'study_permit_expiry_date']


class ResumeForm(forms.ModelForm):
    ''' Resume form '''
    class Meta:
        model = Resume
        fields = ['user', 'uploaded']
        labels = {
            'uploaded': ''
        }
        widgets = {
            'user': forms.HiddenInput()
        }


class AvatarForm(forms.ModelForm):
    ''' Avatar form '''
    class Meta:
        model = Avatar
        fields = ['user', 'uploaded']
        labels = {
            'uploaded': ''
        }
        widgets = {
            'user': forms.HiddenInput()
        }
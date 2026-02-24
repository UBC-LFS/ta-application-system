from django import forms
from django.forms import ModelMultipleChoiceField
from django_summernote.widgets import SummernoteWidget
from administrators.models import *
import datetime as dt

ROLES = {
    'Superadmin': 1,
    'Admin': 2,
    'HR': 3,
    'Instructor': 4,
    'Student': 5
}

def current_year():
    return dt.date.today().year


class CourseCodeForm(forms.ModelForm):
    class Meta:
        model = CourseCode
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'name': 'This field is unique. Maximum characters is 5.'
        }

class CourseNumberForm(forms.ModelForm):
    class Meta:
        model = CourseNumber
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'name': 'This field is unique. Maximum characters is 5.'
        }

class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'name': 'This field is unique. Maximum characters is 12.'
        }

class TermForm(forms.ModelForm):
    ''' Create a model form for a term '''
    class Meta:
        model = Term
        fields = ['code', 'name', 'by_month', 'max_hours',]
        widgets = {
            'code': forms.TextInput(attrs={ 'class': 'form-control' }),
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'by_month': forms.NumberInput(attrs={ 'class': 'form-control' }),
            'max_hours': forms.NumberInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'code': 'This field is unique and maximum characters: 20',
            'by_month': 'Minimun value: 1, Maximum Value: 12',
            'max_hours': 'Minimun value: 0, Maximum Value: 4000'
        }

class ClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = ['year', 'name', 'wage', 'is_active']
        widgets = {
            'year': forms.TextInput(attrs={ 'class': 'form-control' }),
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'wage': forms.NumberInput(attrs={ 'class': 'form-control' })
        }
        help_texts = {
            'year': 'Maximum characters: 10',
            'name': 'Maximum characters: 10'
        }

class CourseForm(forms.ModelForm):
    ''' Create a model form for a course '''
    class Meta:
        model = Course
        fields = ['term', 'code', 'number', 'section', 'name', 'overview', 'job_description', 'job_note', 'is_active']
        widgets = {
            'term': forms.Select(attrs={ 'class': 'form-control' }),
            'code': forms.Select(attrs={ 'class': 'form-control' }),
            'number': forms.Select(attrs={ 'class': 'form-control' }),
            'section': forms.Select(attrs={ 'class': 'form-control' }),
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'overview': SummernoteWidget(),
            'job_description': SummernoteWidget(),
            'job_note': SummernoteWidget()
        }
        labels = {
            'overview': 'Course Overview',
            'job_description': 'Job Description',
            'job_note': 'Note'
        }
        help_texts = {
            'term': 'This field is required.',
            'code': 'This field is required.',
            'number': 'This field is required.',
            'section': 'This field is required.',
            'name': 'This field is required. Maximum 256 characters allowed.'
        }

    field_order = ['term', 'code', 'number','section', 'name', 'overview', 'job_description', 'job_note', 'is_active']


class CourseEditForm(forms.ModelForm):
    ''' Create a model form for a course '''
    class Meta:
        model = Course
        fields = ['name', 'overview', 'job_description', 'job_note', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'overview': SummernoteWidget(),
            'job_description': SummernoteWidget(),
            'job_note': SummernoteWidget()
        }
        labels = {
            'overview': 'Course Overview',
            'job_description': 'Job Description',
            'job_note': 'Note'
        }
        help_texts = {
            'name': 'This field is required. Maximum 256 characters allowed.'
        }

    field_order = ['name', 'overview', 'job_description', 'job_note', 'is_active']


class SessionForm(forms.ModelForm):
    ''' Create a model form for a Session '''

    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note', 'is_visible', 'is_archived']
        widgets = {
            'year': forms.TextInput(attrs={ 'class': 'form-control' }),
            'term': forms.Select(attrs={ 'class': 'form-control' }),
            'title': forms.TextInput(attrs={ 'class': 'form-control' }),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        help_texts = {
            'year': 'Maximum 4 characters allowed.',
            'title': 'Maximum 256 characters allowed.',
            'description': 'This field is optional.',
            'note': 'This field is optional.'
        }

    field_order = ['year', 'term', 'title', 'description', 'note', 'is_visible', 'is_archived']


class SessionEditForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['title', 'description', 'note', 'is_visible', 'is_archived']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }


class SessionConfirmationForm(forms.ModelForm):
    ''' Create a model form for a Session '''

    title = forms.CharField(
        initial='TA Application',
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )
    courses = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note', 'courses', 'is_visible', 'is_archived']
        widgets = {
            'year': forms.HiddenInput(),
            'term': forms.HiddenInput(),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }

    field_order = ['year', 'term', 'title', 'description', 'note', 'courses', 'is_visible', 'is_archived']

    def __init__(self, *args, **kwargs):
        super(SessionConfirmationForm, self).__init__(*args, **kwargs)

        # Get courses with each term
        if 'initial' in kwargs.keys() and kwargs['initial']['term']:
            term = kwargs['initial']['term']
            self.fields['courses'].queryset = Course.objects.filter(term__id=term.id)


class MyModelMultipleChoiceField(ModelMultipleChoiceField):
    ''' Help to display user's full name for queryset in ModelMultipleChoiceField '''
    def label_from_instance(self, obj):
        return obj.get_full_name()


class AdminJobEditForm(forms.ModelForm):
    ''' '''
    assigned_ta_hours = forms.FloatField(
        label='Total Assigned TA Hours',
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
        help_text='Valid range is 0 to 4000.'
    )
    accumulated_ta_hours = forms.FloatField(
        label='Accumulated TA Hours',
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )
    class Meta:
        model = Job
        fields = ['course_overview', 'description', 'note', 'assigned_ta_hours', 'accumulated_ta_hours', 'is_active']
        widgets = {
            'course_overview': SummernoteWidget(),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        labels = {
            'course_overview': 'Course Overview',
            'description': 'Job Description'
        }
    field_order = ['course_overview', 'description', 'note', 'assigned_ta_hours', 'accumulated_ta_hours', 'is_active']

class InstructorUpdateForm(forms.ModelForm):
    ''' To delete job instructors '''
    class Meta:
        model = Job
        fields = ['instructors']


class InstructorJobForm(forms.ModelForm):
    ''' Create a model form for job details of an instructor '''
    class Meta:
        model = Job
        fields = ['course_overview', 'description', 'note']
        widgets = {
            'course_overview': SummernoteWidget(),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        labels = {
            'course_overview': 'Course Overview',
            'description': 'Job Description'
        }


class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['sta_confirmation']


class ReassignApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['note', 'is_declined_reassigned']
        widgets = {
            'note': SummernoteWidget()
        }
        labels = {
            'note': 'Instructor Note',
            'is_declined_reassigned': 'Are you sure to decline and re-assign this application?'
        }
        help_texts = {
            'note': 'This note is visible only to administrators and instructors.'
        }

class TerminateApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['note', 'is_terminated']
        widgets = {
            'note': SummernoteWidget()
        }
        labels = {
            'note': 'Instructor Note',
            'is_terminated': 'Are you sure to terminate this application?'
        }
        help_texts = {
            'note': 'This note is visible only to administrators and instructors.'
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = ApplicationStatus
        fields = ['application', 'assigned', 'assigned_hours', 'has_contract_read']
        widgets = {
            'assigned': forms.HiddenInput()
        }

class ApplicationStatusReassignForm(forms.ModelForm):
    class Meta:
        model = ApplicationStatus
        fields = ['application', 'assigned', 'assigned_hours', 'parent_id']
        widgets = {
            'assigned': forms.HiddenInput()
        }


class ApplicationNoteForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['note']
        widgets = {
            'note': SummernoteWidget()
        }
        labels = {
            'note': 'Instructor Note'
        }
        help_texts = {
            'note': 'This note is visible only to administrators and instructors.'
        }

class AdminApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['classification', 'note']
        widgets = {
            'note': forms.Textarea(attrs={ 'rows': 2 })
        }

class ApplicationForm(forms.ModelForm):
    ''' Create a model form for an application for students '''
    how_qualified = forms.ChoiceField(
        choices=Application.PREFERENCE_CHOICES,
        label='How qualifed are you?'
    )
    how_interested = forms.ChoiceField(
        choices=Application.PREFERENCE_CHOICES,
        label='How interested are you?'
    )

    class Meta:
        model = Application
        fields = ['applicant', 'job','supervisor_approval', 'how_qualified', 'how_interested', 'availability', 'availability_note']
        widgets = {
            'applicant': forms.HiddenInput(),
            'job': forms.HiddenInput(),
            'availability_note': SummernoteWidget()
        }
        labels = {
            'supervisor_approval': 'Supervisor Approval:',
            'availability': 'Availability Requirements:',
            'availability_note': 'Availability Notes:'
        }
        help_texts = {
            'supervisor_approval': "I have my graduate supervisor's or Professional Master's Degree Program Director's approval to TA up to a maximum of 12 hours/week.",
            'availability_note': 'This field is optional.'
        }

class AdminDocumentsForm(forms.ModelForm):
    class Meta:
        model = AdminDocuments
        fields = [
            'application', 'position_number', 'pin', 'tasm', 'processed', 'worktag', 'processing_note'
        ]


class FavouriteForm(forms.ModelForm):
    class Meta:
        model = Favourite
        fields = ['applicant', 'job', 'is_selected']


class EmailForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={ 'class':'form-control' })
    )
    class Meta:
        model = Email
        fields = ['sender', 'receiver','title', 'message', 'type']
        widgets = {
            'message': SummernoteWidget(),
            'sender': forms.HiddenInput(),
            'receiver': forms.HiddenInput(),
            'type': forms.HiddenInput()
        }

class ReminderForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={ 'class':'form-control' })
    )
    class Meta:
        model = Email
        fields = ['application', 'sender', 'receiver', 'title', 'message', 'type']
        widgets = {
            'application': forms.HiddenInput(),
            'message': SummernoteWidget(),
            'sender': forms.HiddenInput(),
            'receiver': forms.HiddenInput(),
            'type': forms.HiddenInput()
        }


class AdminEmailForm(forms.ModelForm):
    class Meta:
        model = AdminEmail
        fields = ['title', 'message', 'type']
        widgets = {
            'title': forms.TextInput(attrs={ 'class':'form-control' }),
            'message': SummernoteWidget(),
            'type': forms.TextInput(attrs={ 'class':'form-control' }),
        }

class LandingPageForm(forms.ModelForm):
    class Meta:
        model = LandingPage
        fields = ['title', 'message', 'notice', 'is_visible']
        widgets = {
            'title': forms.TextInput(attrs={ 'class':'form-control' }),
            'message': SummernoteWidget(),
            'notice': SummernoteWidget()
        }
        help_texts = {
            'title': 'This field is optional. Maximum length is 256 characters.',
            'message': 'This field is optional.',
            'notice': 'This field is optional.'
        }

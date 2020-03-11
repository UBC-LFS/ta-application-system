from django import forms
from django.contrib.auth.models import User
from django.forms import ModelMultipleChoiceField
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

from administrators.models import *
from users.models import Role

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
            'name': 'This field is unique. Maximum characters is 5.'
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
        fields = ['term', 'code', 'number', 'section', 'name', 'overview', 'job_description', 'job_note']
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
            'job_description': 'Job Description',
            'job_note': 'Job Note'
        }
        help_texts = {
            'term': 'This field is required.',
            'code': 'This field is required.',
            'number': 'This field is required.',
            'section': 'This field is required.',
            'name': 'This field is required. Maximum 256 characters allowed.',
            'overview': 'This field is optional.',
            'job_description': 'This field is optional.',
            'job_note': 'This field is optional.'
        }

    field_order = ['term', 'code', 'number','section', 'name', 'overview', 'job_description', 'job_note']


class CourseEditForm(forms.ModelForm):
    ''' Create a model form for a course '''
    class Meta:
        model = Course
        fields = ['name', 'overview', 'job_description', 'job_note']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'overview': SummernoteWidget(),
            'job_description': SummernoteWidget(),
            'job_note': SummernoteWidget()
        }
        labels = {
            'job_description': 'Job Description',
            'job_note': 'Job Note'
        }
        help_texts = {
            'name': 'This field is required. Maximum 256 characters allowed.',
            'overview': 'This field is optional.',
            'job_description': 'This field is optional.',
            'job_note': 'This field is optional.'
        }

    field_order = ['name', 'overview', 'job_description', 'job_note']




class SessionForm(forms.ModelForm):
    ''' Create a model form for a Session '''
    year = forms.CharField(
        max_length=4,
        initial=current_year(),
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
        help_text='This field is required.'
    )
    title = forms.CharField(
        max_length=256,
        initial='TA Application',
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
        help_text='This field is required. Maximum 256 characters allowed.'
    )

    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note']
        widgets = {
            'term': forms.Select(attrs={ 'class': 'form-control' }),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        help_texts = {
            'term': 'This field is required.',
            'description': 'This field is optional.',
            'note': 'This field is optional.'
        }

    field_order = ['year', 'term', 'title', 'description', 'note']

class SessionConfirmationForm(forms.ModelForm):
    ''' Create a model form for a Session '''

    this_year = current_year()
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


class AdminJobForm(forms.ModelForm):
    ''' '''
    assigned_ta_hours = forms.FloatField(
        label='Total Assigned TA Hours',
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
        help_text='This field is required. Valid range is 0 to 4000.'
    )
    instructors = MyModelMultipleChoiceField(
        queryset=User.objects.filter(profile__roles=ROLES['Instructor']).order_by('first_name'),
        widget=forms.CheckboxSelectMultiple(),
        help_text='This field is optional.'
    )
    class Meta:
        model = Job
        fields = ['course_overview', 'description', 'note', 'instructors', 'assigned_ta_hours', 'is_active']
        widgets = {
            'course_overview': SummernoteWidget(),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        labels = {
            'course_overview': 'Course Overview'
        }
        help_texts = {
            'course_overview': 'This field is optional.',
            'description': 'This field is optional.',
            'note': 'This field is optional.'
        }
    field_order = ['course_overview', 'description', 'note', 'assigned_ta_hours', 'is_active', 'instructors']

class AdminJobEditForm(forms.ModelForm):
    ''' '''
    assigned_ta_hours = forms.FloatField(
        label='Total Assigned TA Hours',
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
        help_text='This field is required. Valid range is 0 to 4000.'
    )

    class Meta:
        model = Job
        fields = ['course_overview', 'description', 'note', 'assigned_ta_hours', 'is_active']
        widgets = {
            'course_overview': SummernoteWidget(),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }
        labels = {
            'course_overview': 'Course Overview'
        }
        help_texts = {
            'course_overview': 'This field is optional.',
            'description': 'This field is optional.',
            'note': 'This field is optional.'
        }
    field_order = ['course_overview', 'description', 'note', 'assigned_ta_hours', 'is_active']


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
            'course_overview': 'Course Overview'
        }
        help_texts = {
            'course_overview': 'This field is optional.',
            'description': 'This field is optional.',
            'note': 'This field is optional.'
        }



class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['instructor_preference']
        labels = {
            'instructor_preference': ''
        }

class ReassignApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['note', 'is_declined_reassigned']
        widgets = {
            'note': SummernoteWidget()
        }
        labels = {
            'is_declined_reassigned': 'Are you sure to decline and re-assign this application?'
        }
        help_texts = {
            'note': 'Administrators and instructors can see this note.'
        }

class TerminateApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['note', 'is_terminated']
        widgets = {
            'note': SummernoteWidget()
        }
        labels = {
            'is_terminated': 'Are you sure to terminate this application?'
        }
        help_texts = {
            'note': 'Administrators and instructors can see this note.'
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = ApplicationStatus
        fields = ['application', 'assigned', 'assigned_hours']
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
        help_texts = {
            'note': 'Administrators and instructors can see this note.'
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
        label='How qualifed are you?',
        help_text='This field is required.'
    )
    how_interested = forms.ChoiceField(
        choices=Application.PREFERENCE_CHOICES,
        label='How interested are you?',
        help_text='This field is required.'
    )

    class Meta:
        model = Application
        fields = ['applicant', 'job','supervisor_approval', 'how_qualified', 'how_interested', 'availability', 'availability_note']
        widgets = {
            'applicant': forms.HiddenInput(),
            'job': forms.HiddenInput(),
            'availability_note': forms.Textarea(attrs={ 'rows':2, 'class':'form-control' })
        }
        labels = {
            'supervisor_approval': 'Supervisor Approval',
            'availability': 'Availability requirements',
            'availability_note': 'Availability notes'
        }
        help_texts = {
            'supervisor_approval': 'My supervisor has approved for me to TA up to a maximum of 12 hours/week.',
            'availability_note': 'This field is optional.'
        }

class AdminDocumentsForm(forms.ModelForm):
    class Meta:
        model = AdminDocuments
        fields = [
            'application', 'pin', 'tasm', 'eform', 'speed_chart', 'processing_note'
        ]
        labels = {
            'pin': 'PIN',
            'tasm': 'TASM',
            'eform': 'eForm',
            'speed_chart': 'Speed Chart',
            'processing_note': 'Processing Note'
        }
        widgets = {
            'application': forms.HiddenInput(),
            'pin': forms.TextInput(attrs={ 'class':'form-control' }),
            'eform': forms.TextInput(attrs={ 'class':'form-control' }),
            'speed_chart': forms.TextInput(attrs={ 'class':'form-control' }),
            'processing_note': forms.Textarea(attrs={ 'class':'form-control', 'rows': 2 })
        }
        help_texts = {
            'pin': 'This field is optional. Maximum length is 4.',
            'tasm': 'This field is optional.',
            'eform': 'This field is optional. Maximum length is 6.',
            'speed_chart': 'This field is optional. Maximum length is 4.',
            'processing_note': 'This field is optional.'
        }


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

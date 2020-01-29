from django import forms
from django.contrib.auth.models import User
from django.forms import ModelMultipleChoiceField
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

from administrators.models import *
from users.models import Role

import datetime as dt


#ROLES = { role.name: role.id for role in Role.objects.all() }
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

class CourseNumberForm(forms.ModelForm):
    class Meta:
        model = CourseNumber
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
        }

class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
        }

class TermForm(forms.ModelForm):
    ''' Create a model form for a term '''
    class Meta:
        model = Term
        fields = ['code', 'name']
        widgets = {
            'code': forms.TextInput(attrs={ 'class': 'form-control' }),
            'name': forms.TextInput(attrs={ 'class': 'form-control' })
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

class CourseForm(forms.ModelForm):
    ''' Create a model form for a course '''
    class Meta:
        model = Course
        fields = ['code', 'number','section', 'name', 'term']
        widgets = {
            'code': forms.Select(attrs={ 'class': 'form-control' }),
            'number': forms.Select(attrs={ 'class': 'form-control' }),
            'section': forms.Select(attrs={ 'class': 'form-control' }),
            'name': forms.TextInput(attrs={ 'class': 'form-control' }),
            'term': forms.Select(attrs={ 'class': 'form-control' })
        }

    field_order = ['code', 'number','section', 'name', 'term']


class SessionForm(forms.ModelForm):
    ''' Create a model form for a Session '''
    next_year = current_year() + 1
    year = forms.CharField(
        max_length=4,
        initial=next_year,
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )
    title = forms.CharField(
        initial='TA Application',
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )

    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note']
        widgets = {
            'term': forms.Select(attrs={ 'class': 'form-control' }),
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
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
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )
    assigned_ta_hours = forms.FloatField(
        label='Assigned TA Hours',
        widget=forms.TextInput(attrs={ 'class': 'form-control' }),
    )
    instructors = MyModelMultipleChoiceField(
        queryset=User.objects.filter(profile__roles=ROLES['Instructor']).order_by('pk'),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Job
        fields = ['title', 'description', 'qualification', 'note', 'instructors', 'assigned_ta_hours', 'is_active']
        widgets = {
            'description': SummernoteWidget(),
            'note': SummernoteWidget(),
            'qualification': SummernoteWidget()
        }
    field_order = ['title', 'description', 'qualification', 'note', 'assigned_ta_hours', 'is_active', 'instructors']


class InstructorJobForm(forms.ModelForm):
    ''' Create a model form for job details of an instructor '''
    title = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={ 'class': 'form-control' })
    )
    class Meta:
        model = Job
        fields = ['title', 'description', 'qualification', 'note']
        widgets = {
            'description': SummernoteWidget(),
            'qualification': SummernoteWidget(),
            'note': SummernoteWidget()
        }

class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['instructor_preference']
        labels = {
            'instructor_preference': ''
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


class SessionJobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['session', 'course']


class JobForm(forms.ModelForm):
    instructors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__roles=ROLES['Instructor']),
        widget=forms.CheckboxSelectMultiple()
    )
    class Meta:
        model = Job
        fields = ['title', 'description', 'qualification', 'note', 'instructors', 'is_active']


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

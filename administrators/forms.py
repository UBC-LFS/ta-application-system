from django import forms
from django.contrib.auth.models import User
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

from .models import *

import datetime as dt


ROLES = {
    'Student': 1,
    'Instructor': 2,
    'Hr': 3,
    'Admin': 4,
    'Superadmin': 5
}

def current_year():
    return dt.date.today().year

class CourseCodeForm(forms.ModelForm):
    class Meta:
        model = CourseCode
        fields = ['name']

class CourseNumberForm(forms.ModelForm):
    class Meta:
        model = CourseNumber
        fields = ['name']

class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        fields = ['name']


#checked
class TermForm(forms.ModelForm):
    """ Create a model form for a term """
    class Meta:
        model = Term
        fields = ['code', 'name']


class ClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = ['year', 'name', 'wage', 'is_active']

class CourseForm(forms.ModelForm):
    ''' Create a model form for a course '''
    class Meta:
        model = Course
        fields = ['code', 'number','section', 'name', 'term']

    field_order = ['code', 'number','section', 'name', 'term']


class SessionForm(forms.ModelForm):
    ''' Create a model form for a Session '''
    next_year = current_year() + 1
    year = forms.CharField(initial=next_year)
    title = forms.CharField(initial='TA Application')
    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note']
        widgets = {
            'description': SummernoteWidget(),
            'note': SummernoteWidget()
        }

    field_order = ['year', 'term', 'title', 'description', 'note']


# checked
class SessionConfirmationForm(forms.ModelForm):
    """ Create a model form for a Session """
    this_year = current_year()
    year = forms.CharField(initial=this_year)
    title = forms.CharField(initial='TA Application')
    courses = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note', 'courses', 'is_visible', 'is_archived']
        widgets = {
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

class AdminJobForm(forms.ModelForm):
    instructors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(profile__roles=ROLES['Instructor']),
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
    class Meta:
        model = Job
        fields = ['title', 'description', 'qualification', 'note']
        widgets = {
            'description': SummernoteWidget(),
            'qualification': SummernoteWidget(),
            'note': SummernoteWidget()
        }

# checked
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


# to be checked
class AdminApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['classification', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows':2})
        }

#checked
class ApplicationForm(forms.ModelForm):
    """ Create a model form for an application for students """
    how_qualified = forms.ChoiceField(choices=Application.PREFERENCE_CHOICES, widget=forms.RadioSelect)
    how_interested = forms.ChoiceField(choices=Application.PREFERENCE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Application
        fields = ['applicant', 'job','supervisor_approval', 'how_qualified', 'how_interested', 'availability', 'availability_note']
        widgets = {
            'applicant': forms.HiddenInput(),
            'job': forms.HiddenInput(),
            'availability_note': forms.Textarea(attrs={'rows':2})
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


class EmailForm(forms.ModelForm):
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
    class Meta:
        model = Email
        fields = ['application', 'sender', 'receiver','title', 'message', 'type']
        widgets = {
            'application': forms.HiddenInput(),
            'message': SummernoteWidget(),
            'sender': forms.HiddenInput(),
            'receiver': forms.HiddenInput(),
            'type': forms.HiddenInput()
        }

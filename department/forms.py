from django import forms
from django.contrib.auth.models import User

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

# checked
class CourseForm(forms.ModelForm):
    """ Create a model form for a course """
    class Meta:
        model = Course
        fields = ['code', 'number','section', 'name', 'term']

    field_order = ['code', 'number','section', 'name', 'term']


# checked
class SessionForm(forms.ModelForm):
    """ Create a model form for a Session """
    this_year = current_year()
    year = forms.CharField(initial=this_year)
    title = forms.CharField(initial='TA Application')
    class Meta:
        model = Session
        fields = ['year', 'term', 'title', 'description', 'note', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows':2}),
            'note': forms.Textarea(attrs={'rows':2})
        }

    field_order = ['year', 'term', 'title', 'description', 'note', 'is_active']


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
        fields = ['year', 'term', 'title', 'description', 'note', 'is_active', 'courses']
        widgets = {
            'description': forms.Textarea(attrs={'rows':2}),
            'note': forms.Textarea(attrs={'rows':2})
        }

    field_order = ['year', 'term', 'title', 'description', 'note', 'is_active', 'courses']

    def __init__(self, *args, **kwargs):
        super(SessionConfirmationForm, self).__init__(*args, **kwargs)

        # Get courses with each term
        if 'initial' in kwargs.keys() and kwargs['initial']['term']:
            term = kwargs['initial']['term']
            self.fields['courses'].queryset = Course.objects.filter(term__id=term.id)




# checked
class InstructorJobForm(forms.ModelForm):
    """ Create a model form for job details of an instructor """
    class Meta:
        model = Job
        fields = ['title', 'description', 'qualification', 'note']

# checked
class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['instructor_preference']
        labels = {
            'instructor_preference': ''
        }

#checked
class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = ApplicationStatus
        fields = ['assigned', 'assigned_hours']
        widgets = {
            'assigned': forms.HiddenInput()
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

class AdminApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['classification', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows':2})
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

from django import template
from django.http import Http404
from administrators.models import Session

register = template.Library()

@register.filter
def replace_session(session):
    if not session: return None

    found = Session.objects.filter(slug=session, is_visible=True, is_archived=False)
    if not found.exists(): 
        raise Http404
        
    splitted = session.split('-')
    return '{0} {1}'.format(splitted[0], splitted[1].capitalize())

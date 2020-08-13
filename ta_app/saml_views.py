from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from users import api as userApi
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from accounts import views as accountView

def init_saml_auth(req):
    return OneLogin_Saml2_Auth(req, custom_base_path=settings.SAML_FOLDER)


def prepare_django_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        #'server_port': request.META['SERVER_PORT'],
        'server_port': request.META['HTTP_X_FORWARDED_PORT'],
        'get_data': request.GET.copy(),
        # Uncomment if using ADFS as IdP, https://github.com/onelogin/python-saml/pull/144
        # 'lowercase_urlencoding': True,
        'post_data': request.POST.copy()
    }
    return result

def authenticate(saml_authentication=None):
    """ Create a new user if the user does not exist; otherwise, return a user """

    if not saml_authentication:
        return None

    if saml_authentication.is_authenticated():
        user_data = {
            'first_name': None,
            'last_name': None,
            'username': None,
            'email': None,
            'employee_number': None,
            'student_number': None
        }

        for key, value in saml_authentication.get_attributes().items():
            if '100.1.1' in key:
                user_data['username'] = value[0]
            elif '100.1.3' in key:
                user_data['email'] = value[0]
            elif '2.5.4.42' in key:
                user_data['first_name'] = value[0]
            elif '2.5.4.4' in key:
                user_data['last_name'] = value[0]
            elif '3.1.3' in key:
                user_data['employee_number'] = value[0]
            elif 'ubcEduStudentNumber' in key:
                user_data['student_number'] = value[0]

        user = userApi.user_exists(user_data)
        if user == None:
            user = userApi.create_user(user_data)
        return user
    return None

@csrf_exempt
def saml(request, action=None):
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    if 'SAMLResponse' in req['get_data']:
        req['get_data']['sls'] = ''

    # Redirect to idp
    if 'sso' in req['get_data']:
        return HttpResponseRedirect(auth.login())

    if 'slo' in req['get_data']:
        name_id = None
        session_index = None
        name_id_format = None

        if 'samlNameId' in request.session:
            name_id = request.session['samlNameId']
        if 'samlSessionIndex' in request.session:
            session_index = request.session['samlSessionIndex']
        if 'samlNameIdFormat' in request.session:
            name_id_format = request.session['samlNameIdFormat']

        # Login was not done through saml
        if not name_id and not session_index:
            #return HttpResponseRedirect(settings.LOGIN_URL)
            return redirect('accounts:login')

        # Redirect to the saml logout
        #return HttpResponseRedirect(auth.logout(name_id=name_id, session_index=session_index))
        return HttpResponseRedirect( auth.logout(name_id=name_id, session_index=session_index, name_id_format=name_id_format) )

    # Paths from idp
    if 'acs' in req['get_data']:
        auth.process_response()
        errors = auth.get_errors()

        if not errors:
            if auth.is_authenticated():
                request.session['samlUserdata'] = auth.get_attributes()
                request.session['samlNameId'] = auth.get_nameid()
                request.session['samlSessionIndex'] = auth.get_session_index()
                request.session['samlNameIdFormat'] = auth.get_nameid_format()

                user = authenticate(saml_authentication=auth)
                login(request, user)

                if 'RelayState' in req['post_data'] and OneLogin_Saml2_Utils.get_self_url(req) != req['post_data']['RelayState']:
                    #return HttpResponseRedirect(auth.redirect_to(req['post_data']['RelayState']))
                    roles = userApi.get_user_roles(user)
                    request.session['loggedin_user'] = {
                        'id': user.id,
                        'username': user.username,
                        'roles': roles
                    }
                    redirect_to = accountView.redirect_to_index_page(roles)
                    return HttpResponseRedirect(redirect_to)

                else:
                    for attr_name in request.session['samlUserdata'].keys():
                        print('%s ==> %s' % (attr_name, '|| '.join(request.session['samlUserdata'][attr_name])))
            else:
             print('Not authenticated')
        else:
            print("Error when processing SAML Response: %s" % (', '.join(errors)))

    elif 'sls' in req['get_data']:
        #dscb = lambda: request.session.flush()
        #url = auth.process_slo(delete_session_cb=dscb)
        errors = auth.get_errors()

        request.session.flush()
        logout(request)
        if not errors:
            return HttpResponseRedirect(settings.SAML_LOGOUT_URL)
        else:
            return HttpResponseRedirect(settings.LOGIN_URL)

    return render(request, 'accounts/login.html', {
        'errors': errors,
        'error_reason': error_reason,
        'not_auth_warn': not_auth_warn,
        'success_slo': success_slo,
        'attributes': attributes,
        'paint_logout': paint_logout
    })

def attrs(request):
    paint_logout = False
    attributes = False

    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()

    return render(request, 'ta_app/attrs.html', {
        'paint_logout': paint_logout,
        'attributes': attributes
    })


def metadata(request):
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    saml_settings = auth.get_settings()
    #saml_settings = OneLogin_Saml2_Settings(settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp

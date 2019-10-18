
from django.shortcuts import render, redirect


"""
@login_required(login_url=settings.LOGIN_URL)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@require_http_methods(['GET', 'POST'])
def hr(request):
    ''' Display HR's page '''

    if not api.is_valid_user(request.user): raise PermissionDenied
    loggedin_user = api.loggedin_user(request.user)
    if  'Admin' not in loggedin_user['roles'] or 'HR' not in loggedin_user['roles']: raise PermissionDenied

    users = api.get_users()
    total_users = len(users)

    # Pagination enables
    '''
    user_list = api.get_users()
    total_users = len(user_list)
    query = request.GET.get('q')
    if query:
        user_list = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        ).distinct()

    page = request.GET.get('page', 1)
    paginator = Paginator(user_list, 5) # Set 10 users in a page
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    '''


    return render(request, 'users/hr/hr.html', {
        'loggedin_user': api.loggedin_user(request.user),
        'users': users,
        'total_users': total_users,
    })

"""
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from tastypie.models import ApiKey


def api_key(request):
    app_dict = {
        'name': 'Account',
        'app_label': 'Account',
        'app_url': '',
        'has_module_perms': False,
        'models': [
            {
                'name': 'Api key',
                'object_name': 'Api key',
                'perms': [],
                'admin_url': '/account/api-key'
            }
        ],
    }

    context = {
        'title': 'Account - api key',
        'app_list': [app_dict],
        'api_key': None,
        'has_permission': True
    }

    if hasattr(request.user, 'api_key'):
        context['api_key'] = request.user.api_key

    return TemplateResponse(request, 'api_key.html', context)


def generate_api_key(request):
    if hasattr(request.user, 'api_key') is False:
        ApiKey.objects.create(user=request.user)

    return redirect('api_key')

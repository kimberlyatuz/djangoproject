from django.conf import settings
from django.contrib.auth.models import Group
from .models import User


def site_info(request):
    """Adds site-wide information to template context"""
    return {
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SITE_NAME': settings.SITE_NAME,
        'DEBUG': settings.DEBUG
    }


def user_roles(request):
    """Adds user role information to template context"""
    if not request.user.is_authenticated:
        return {
            'has_profile': False,
            'user_role': None,
            'is_approved': False,
            'is_profile_active': False,
            'user_groups': []
        }

    try:
        # Get user's groups
        groups = list(request.user.groups.values_list('name', flat=True))

        return {
            'user_role': request.user.role,
            'is_doctor': request.user.role == 'doctor',
            'is_nurse': request.user.role == 'nurse',
            'is_admin': request.user.role == 'admin',
            'is_staff': request.user.role == 'staff',
            'is_approved': request.user.is_approved,
            'is_profile_active': request.user.is_active,
            'has_profile': True,
            'user_groups': groups,
            'is_superuser': request.user.is_superuser,
            # Permission flags
            'can_approve_users': request.user.has_perm('app1.approve_users'),
            'can_manage_patients': request.user.has_perm('app1.change_patientdemographics'),
            'can_manage_forms': request.user.has_perm('app1.change_userform')
        }
    except AttributeError:
        # Handle case where custom user attributes aren't available
        return {
            'has_profile': False,
            'user_role': None,
            'is_approved': False,
            'is_profile_active': False,
            'user_groups': []
        }


def group_permissions(request):
    """Adds group permission information to template context"""
    if not request.user.is_authenticated:
        return {'group_permissions': {}}

    permissions = {}
    for group in request.user.groups.all():
        permissions[group.name] = [perm.codename for perm in group.permissions.all()]

    return {
        'group_permissions': permissions,
        'all_permissions': list(request.user.get_all_permissions())
    }
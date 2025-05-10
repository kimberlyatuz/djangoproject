from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import User, RegistrationToken

# Default groups with their permissions
GROUP_PERMISSIONS = {
    'Administrators': [
        'add_user', 'change_user', 'delete_user', 'view_user',
        'add_patientdemographics', 'change_patientdemographics',
        'delete_patientdemographics', 'view_patientdemographics',
        'approve_users'
    ],
    'Doctors': [
        'add_patientdemographics', 'change_patientdemographics',
        'view_patientdemographics', 'add_formsubmission',
        'change_formsubmission', 'view_formsubmission'
    ],
    'Nurses': [
        'add_patientdemographics', 'change_patientdemographics',
        'view_patientdemographics', 'add_formsubmission',
        'view_formsubmission'
    ],
    'Staff': [
        'view_patientdemographics', 'add_formsubmission',
        'view_formsubmission'
    ]
}

@receiver(post_migrate)
def create_default_groups_and_permissions(sender, **kwargs):
    """Create default groups and assign permissions when database is ready"""
    # Create groups
    for group_name in GROUP_PERMISSIONS.keys():
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            # Assign permissions to the group
            for perm_codename in GROUP_PERMISSIONS[group_name]:
                try:
                    # Split permission codename to get app_label and model
                    action, model_name = perm_codename.split('_', 1)
                    # Get the content type
                    ct = ContentType.objects.get(app_label='app1', model=model_name)
                    # Get the permission
                    perm = Permission.objects.get(content_type=ct, codename=perm_codename)
                    group.permissions.add(perm)
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    continue

@receiver(post_save, sender=User)
def handle_user_profile_and_groups(sender, instance, created, **kwargs):
    """
    Handle user group assignments when User is saved
    """
    # Auto-approve and activate superusers
    if instance.is_superuser:
        instance.is_active = True
        instance.is_approved = True
        instance.approved_by = instance
        instance.approved_at = timezone.now()
        instance.save(update_fields=['is_active', 'is_approved', 'approved_by', 'approved_at'])

    # Get or create the groups (in case they don't exist yet)
    staff_group, _ = Group.objects.get_or_create(name='Staff')
    admin_group, _ = Group.objects.get_or_create(name='Administrators')
    doctors_group, _ = Group.objects.get_or_create(name='Doctors')
    nurses_group, _ = Group.objects.get_or_create(name='Nurses')

    # Clear all groups first
    instance.groups.clear()

    # Assign base groups
    if instance.is_staff:
        instance.groups.add(staff_group)
    if instance.is_superuser:
        instance.groups.add(admin_group)

    # Assign role-specific groups
    if instance.role == 'doctor':
        instance.groups.add(doctors_group)
    elif instance.role == 'nurse':
        instance.groups.add(nurses_group)
    elif instance.role == 'admin':
        instance.groups.add(admin_group)
    else:  # default staff
        instance.groups.add(staff_group)

    # For new users with registration tokens
    if created and hasattr(instance, 'registration_token'):
        token = instance.registration_token
        token.used = True
        token.save()
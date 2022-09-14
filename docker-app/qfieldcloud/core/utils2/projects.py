from typing import Tuple

from django.db.models import Q
from django.utils.translation import gettext as _
from qfieldcloud.core import invitations_utils as invitation
from qfieldcloud.core import permissions_utils as perms
from qfieldcloud.core.models import Project, ProjectCollaborator, User


def create_collaborator(project: Project, user: User) -> Tuple[bool, str]:
    """Creates a new collaborator (qfieldcloud.core.ProjectCollaborator) if possible

    Args:
        project (Project): the project to add collaborator to
        user (User): the user to be added as collaborator

    Returns:
        Tuple[bool, str]: success, message - whether the collaborator creation was success and explanation message of the outcome
    """
    success, message = False, ""

    try:
        perms.check_can_become_collaborator(user, project)

        # TODO actual invitation, not insertion of already existing user (see TODO about inviting
        # users to create accounts above)
        ProjectCollaborator.objects.create(
            project=project,
            collaborator=user,
        )
        success = True
        message = _('User "{}" has been invited to the project.').format(user.username)
    except perms.UserOrganizationRoleError:
        message = _(
            "User '{}' is not a member of the organization that owns the project. "
            "Please add this user to the organization first."
        ).format(user.username)
    except (
        perms.AlreadyCollaboratorError,
        perms.ReachedCollaboratorLimitError,
        perms.ExpectedPremiumUserError,
    ) as err:
        message = str(err)

    return success, message


def create_collaborator_by_username_or_email(
    project: Project, username: str, created_by: User
):
    """Creates a new collaborator (qfieldcloud.core.ProjectCollaborator) if possible

    Args:
        project (Project): the project to add collaborator to
        user (str): the username or email to be added as collaborator or invited to join QFieldCloud
        created_by (User): the user that initiated the collaborator creation

    Returns:
        Tuple[bool, str]: success, message - whether the collaborator creation was success and explanation message of the outcome
    """
    success, message = False, ""
    users = list(
        User.objects.filter(Q(username=username) | Q(email=username)).exclude(
            type=User.Type.ORGANIZATION
        )
    )

    if len(users) == 0:
        # No user found, if string is an email address, we try to send a link
        if invitation.is_valid_email(username):
            success, message = invitation.invite_user_by_email(username, created_by)
        else:
            message = _('User "{}" does not exist.').format(username)
    elif len(users) > 1:
        # TODO support invitation of multiple users
        message = _("Adding multiple collaborators at once is not supported.").format(
            username
        )
    elif users[0].is_organization:
        message = (
            _(
                'Organization "{}" cannot be added. Only users and teams can be collaborators.'
            ).format(username),
        )
    else:
        success, message = create_collaborator(project, users[0])

    return success, message

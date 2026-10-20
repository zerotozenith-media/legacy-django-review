"""
Access control decorators for the contributor app.

Why this file exists
--------------------
The authorization middleware only inspects a whitelist of URL prefixes. The
"contributor" prefix was not in that list, so every URL under /contributor/
bypassed permission checking entirely.

Unlike the transfer, properties and financial_reports apps, whose views carry
their own @login_required, the contributor views carried no authentication or
role check at all. That left tax receipt generation, donor search, and
donation entry reachable without the checks the system documentation describes.

These decorators enforce the documented policy at the view itself, so
protection no longer depends on the middleware whitelist being correct.

Roles, from authentication.models.User:
    1 MEMBER
    2 LOCAL_CHURCH_PASTOR
    3 NATIONAL_OVERSEER
    4 REGION_OVERSEER
    5 MARRIAGE_RECORDS
    6 DONOR
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from authentication.models import User

# Roles permitted to generate, preview, send or download official tax receipts.
# Local church pastors are deliberately excluded, per system documentation:
# "Only National Overseers and Region Overseers have permission to generate
# and manage tax receipts."
RECEIPT_ROLES = (User.NATIONAL_OVERSEER, User.REGION_OVERSEER)

# Roles permitted to record and view contributions, but not to issue receipts.
CONTRIBUTION_ROLES = (
    User.LOCAL_CHURCH_PASTOR,
    User.NATIONAL_OVERSEER,
    User.REGION_OVERSEER,
)


def _role_required(allowed_roles):
    """
    Build a decorator requiring an authenticated user holding one of
    allowed_roles.

    Anonymous users are redirected to login. Authenticated users without a
    permitted role get the existing 403 page, matching how the middleware
    already handles denials. Superusers always pass.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url="/authentication/login")
        def _wrapped(request, *args, **kwargs):
            user = request.user

            if user.is_superuser:
                return view_func(request, *args, **kwargs)

            if getattr(user, "role", None) in allowed_roles:
                return view_func(request, *args, **kwargs)

            return render(request, "403.html", status=403)

        return _wrapped

    return decorator


#: Only National and Region Overseers may touch tax receipts.
receipt_access_required = _role_required(RECEIPT_ROLES)

#: Pastors and above may record and view contributions.
contribution_access_required = _role_required(CONTRIBUTION_ROLES)

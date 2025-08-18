from rest_framework import permissions

from .models import Organization


class IsOrgAdmin(permissions.BasePermission):
    """Allows access only to organization owners."""

    def has_permission(self, request, view):
        org_pk = view.kwargs.get("org_pk")
        if not request.user or not request.user.is_authenticated:
            return False
        if org_pk is None:
            return False
        return Organization.objects.filter(pk=org_pk, owner=request.user).exists()

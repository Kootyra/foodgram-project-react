from rest_framework import permissions


class IsUserOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.role == 'user'


class IsAuthorUserAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method == 'POST':
            return request.user.is_authenticated

        if request.method in ['PATCH', 'DELETE']:
            return (
                obj.author == request.user
                or request.user.is_superuser
                or request.user.role in ('user', 'admin')
            )
        return request.method in permissions.SAFE_METHODS


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method == 'POST':
            return request.user.is_authenticated

        if request.method in ['PATCH', 'DELETE']:
            return (
                obj.author == request.user
                or request.user.is_superuser
            )
        return request.method in permissions.SAFE_METHODS


class AdminrOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or (request.user.is_authenticated and (
                    request.user.role == 'admin' or request.user.is_superuser)
                    )
                )


class AdminOrUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated and (
                    request.user.role == 'admin'
                    or request.user.role == 'user'
                    or request.user.is_superuser)
                )


class Admin(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated and (
                request.user.role == 'admin' or request.user.is_superuser)
                )

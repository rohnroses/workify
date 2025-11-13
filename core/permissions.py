from rest_framework import permissions

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user.profile, 'role', None) == 'employer'
    
class IsWorker(permissions.BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user.profile, 'role', None) == 'worker'
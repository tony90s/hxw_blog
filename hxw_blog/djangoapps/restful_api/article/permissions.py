from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow author of a article to edit it.
    Assumes the model instance has an `author_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `author_id`.
        return obj.author_id == request.user.id


class IsCommentatorOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow commentator of a comment to edit it.
    Assumes the model instance has an `commentator_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `commentator_id`.
        return obj.commentator_id == request.user.id


class IsReplierOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow replier_id of a comment_reply to edit it.
    Assumes the model instance has an `replier_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `replier_id`.
        return obj.replier_id == request.user.id


class IsPraiseOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owner of a praise to edit it.
    Assumes the model instance has an `user_id` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `user_id`.
        return obj.user_id == request.user.id

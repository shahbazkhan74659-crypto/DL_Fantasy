from .utils import gravatar_url


def avatar(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        if user.google_picture_url:
            return {'avatar_url': user.google_picture_url}
        if user.email:
            return {'avatar_url': gravatar_url(user.email, size=64)}
    return {}

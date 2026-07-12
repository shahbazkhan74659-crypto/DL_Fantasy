from .utils import gravatar_url


def avatar(request):
    user = getattr(request, 'user', None)
    if user and user.is_authenticated and user.email:
        return {'gravatar_url': gravatar_url(user.email, size=64)}
    return {}

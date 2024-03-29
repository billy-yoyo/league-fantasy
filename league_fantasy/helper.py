from django.http import HttpResponseRedirect

def authorized(func):
  def wrapper(request, *args, **kwargs):
    if not request.user.is_authenticated:
      return HttpResponseRedirect("/accounts/login")
    return func(request, *args, **kwargs)
  return wrapper


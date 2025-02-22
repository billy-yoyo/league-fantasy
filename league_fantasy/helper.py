from django.http import HttpResponseRedirect
from .models import Tournament

def authorized(func):
  def wrapper(request, *args, **kwargs):
    print("checking auth")
    if not request.user.is_authenticated:
      return HttpResponseRedirect("/accounts/login")
    return func(request, *args, **kwargs)
  return wrapper

def get_tournament(request, is_post=False):
  if is_post:
    optional_id = request.POST.get("tournament", None)
  else:
    optional_id = request.GET.get("t", None)

  if optional_id is None:
    return Tournament.objects.filter(active=True).first()
  else:
    return Tournament.objects.filter(id=optional_id).first()

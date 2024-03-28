from django.template.defaulttags import register

@register.filter
def keyvalue(dict, key):
    if dict and key in dict:
        return dict.get(key)
    return None

@register.filter
def toint(value):
    return int(value)

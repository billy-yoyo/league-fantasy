from django.template.defaulttags import register

def is_int(x):
    return int(x) == x

@register.filter
def keyvalue(dict, key):
    if dict and key in dict:
        return dict.get(key)
    return None

@register.filter
def toint(value):
    return int(value)

@register.filter
def asdecimal(value):
    floatval = float(value)
    if is_int(floatval):
        return str(int(floatval))
    else:
        return f"{floatval:.2f}"
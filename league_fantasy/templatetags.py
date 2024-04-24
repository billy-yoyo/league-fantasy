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
    if value is not None:
        return int(value)
    return 0

@register.filter
def asdecimal(value):
    floatval = float(value)
    if is_int(floatval):
        return str(int(floatval))
    else:
        return f"{floatval:.2f}"
    
@register.filter
def money(value):
    value = "".join(reversed(str(int(value))))
    parts = [value[i:i+3] for i in range(0, len(value), 3)]
    money = "".join(reversed(",".join(parts)))
    return f"£{money}"

@register.filter
def lower(value):
    return value.lower()

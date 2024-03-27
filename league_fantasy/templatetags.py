from django.template.defaulttags import register

@register.filter
def keyvalue(dict, key):
    if dict and key in dict:
        return dict[key]
    return None

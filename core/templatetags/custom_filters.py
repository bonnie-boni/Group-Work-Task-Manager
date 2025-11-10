from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Ensure the key is a string for dictionary lookup, as ObjectIds are stored as strings in context
    return dictionary.get(str(key))

@register.filter(name='replace')
def replace(value, arg):
    old, new = arg.split(',')
    return value.replace(old, new)

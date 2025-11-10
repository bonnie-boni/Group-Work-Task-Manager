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

@register.filter
def get_item_by_member_id(divisions, member_id):
    """
    Custom filter to get a division dictionary from a list of divisions
    based on the member_id.
    """
    for division in divisions:
        if str(division.get('member_id')) == str(member_id):
            return division
    return None

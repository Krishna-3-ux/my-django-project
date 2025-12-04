from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Fetch the value for a given key from a dictionary."""
    try:
        return dictionary.get(str(key), '')
    except AttributeError:
        return ''  # Return an empty string if key doesn't exist or dictionary is invalid

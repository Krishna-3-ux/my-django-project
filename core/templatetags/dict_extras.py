# In your templatetags/dict_extras.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Returns the value for a given key from the dictionary."""
    return dictionary.get(str(key))  # Ensure key is converted to string

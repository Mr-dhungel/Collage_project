from django import template
from django.shortcuts import get_object_or_404
from voting.models import Post

register = template.Library()

@register.filter
def getattribute(obj, attr):
    """
    Gets an attribute of an object dynamically from a string name.

    Usage:
    {{ form|getattribute:"field_name" }}
    """
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, 'fields') and attr in obj.fields:
        # For Django forms
        return obj[attr]
    elif isinstance(obj, dict) and attr in obj:
        # For dictionaries
        return obj[attr]
    return None

@register.filter
def get_post(post_id):
    """
    Get a post by ID.
    Usage: {{ post_id|get_post }}
    """
    try:
        return get_object_or_404(Post, pk=post_id)
    except:
        return None

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key)

@register.filter
def default_if_none(value, default):
    """
    Return a default value if the value is None.
    Usage: {{ value|default_if_none:"default" }}
    """
    if value is None:
        return default
    return value

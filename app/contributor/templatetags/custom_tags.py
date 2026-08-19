from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, 0)


@register.simple_tag
def reverse_url(name):
    """
    Custom template tag to reverse a URL by its name.
    Usage: {% reverse_url 'name_of_url' %}
    """
    return reverse(name)


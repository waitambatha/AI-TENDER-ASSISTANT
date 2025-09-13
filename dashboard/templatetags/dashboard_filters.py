from django import template
import os

register = template.Library()

@register.filter
def filename_only(filepath):
    """Extract just the filename from a file path"""
    return os.path.basename(filepath)

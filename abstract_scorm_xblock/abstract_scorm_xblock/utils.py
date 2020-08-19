# -*- coding: utf-8 -*-
import pkg_resources

from django.template import Context, Template


def gettext(text):
    """Dummy `gettext` replacement to make string extraction
    tools scrape strings marked for translation """
    return text


def resource_string(path):
    """Handy helper for getting resources from our kit."""
    return pkg_resources.resource_string(__name__, path).decode("utf8")


def render_template(template_path, context):
    template_str = resource_string(template_path)
    template = Template(template_str)
    return template.render(Context(context))

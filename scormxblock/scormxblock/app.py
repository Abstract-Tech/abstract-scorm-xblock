# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import PluginSettings
from openedx.core.djangoapps.plugins.constants import PluginURLs
from openedx.core.djangoapps.plugins.constants import ProjectType
from openedx.core.djangoapps.plugins.constants import SettingsType


class ScormXBlockAppConfig(AppConfig):
    name = "scormxblock"
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: "scormxblock",
                PluginURLs.REGEX: "scormxblock/",
                PluginURLs.RELATIVE_PATH: "views",
            },
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: "scormxblock",
                PluginURLs.REGEX: "scormxblock/",
                PluginURLs.RELATIVE_PATH: "views",
            },
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: "app"},
            },
            ProjectType.CMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: "app"},
            },
        },
    }


def plugin_settings(settings):
    """
    Nothing to do here.
    """
    pass

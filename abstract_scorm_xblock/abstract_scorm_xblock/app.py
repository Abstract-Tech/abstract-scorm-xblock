# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import AppConfig
from openedx.core.djangoapps.plugins.constants import PluginSettings
from openedx.core.djangoapps.plugins.constants import PluginURLs
from openedx.core.djangoapps.plugins.constants import ProjectType
from openedx.core.djangoapps.plugins.constants import SettingsType


class AbstractScormXBlockAppConfig(AppConfig):
    name = "abstract_scorm_xblock"
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: "abstract_scorm_xblock",
                PluginURLs.REGEX: "abstract_scorm_xblock/",
                PluginURLs.RELATIVE_PATH: "views",
            },
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: "abstract_scorm_xblock",
                PluginURLs.REGEX: "abstract_scorm_xblock/",
                PluginURLs.RELATIVE_PATH: "views",
            },
        },
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: "app"},
            },
            ProjectType.CMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: "app"},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: "app"},
            },
        },
    }


def plugin_settings(settings):
    if not getattr(settings, "STORAGE_SCORM_PATH", None):
        # This is used to build the path to the location where the
        # SCORM packages are extracted into the default storage
        # e.g. /scorm_packages/09c1735eaa57d78fe245868f0e07cf7b/index_lms.html
        settings.STORAGE_SCORM_PATH = "scorm_packages"

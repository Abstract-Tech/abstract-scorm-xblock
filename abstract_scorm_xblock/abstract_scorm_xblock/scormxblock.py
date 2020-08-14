# -*- coding: utf-8 -*-
import os
import io
import json
import logging
from zipfile import ZipFile

from webob import Response
from lxml import etree

from django.conf import settings
from django.urls import reverse
from django.core.files.storage import default_storage

from xmodule.contentstore.django import contentstore

from xblock.core import XBlock
from xblock.fields import Scope, String, Float, Boolean, Dict, Integer
from xblock.fragment import Fragment

from .utils import gettext as _
from .utils import resource_string, render_template
from .constants import ScormVersions
from .exceptions import ScormManifestNotFoundException, ScormPackageNotFoundException


logger = logging.getLogger(__name__)


class AbstractScormXBlock(XBlock):

    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default="SCORM unit",
        scope=Scope.settings,
    )
    scorm_file = String(
        display_name=_("SCORM file package"),
        help=_(
            'Name of the SCORM Zip file uploaded through the "Files & Uploads" section of the Course'
        ),
        default="",
        scope=Scope.settings,
    )
    scorm_index = String(
        display_name=_("SCORM index"),
        help=_(
            "Path to the HTML index page in the SCORM package. If left blank we'll try to guess it's location from the SCORM manifest file"
        ),
        default="",
        scope=Scope.settings,
    )
    has_score = Boolean(
        display_name=_("Scored"),
        help=_(
            "Select False if this unit will not receive a numerical score from the SCORM"
        ),
        default=True,
        scope=Scope.settings,
    )
    icon_class = String(
        display_name=_("Icon class"),
        help=_(
            "The icon which will be displayed on the units navigation in courseware"
        ),
        values=[
            {"display_name": "Problem", "value": "problem"},
            {"display_name": "Video", "value": "video"},
            {"display_name": "Other", "value": "other"},
        ],
        default="problem",
        scope=Scope.settings,
    )
    width = Integer(
        display_name=_("Display Width (px)"),
        help=_("Width of the iframe. If empty defaults to 100%"),
        scope=Scope.settings,
    )
    height = Integer(
        display_name=_("Display Height (px)"),
        help=_("Height of iframe. If empty defaults to 450px"),
        default=450,
        scope=Scope.settings,
    )
    popup = Boolean(
        display_name=_("Popup"),
        help=_("Open in a new popup window, or an iframe."),
        default=False,
        scope=Scope.settings,
    )
    autoopen = Boolean(
        display_name=_("Popup on entry"),
        help=_("Should the popup window show on load (instead of on button click)."),
        default=False,
        scope=Scope.settings,
    )
    allowopeninplace = Boolean(
        display_name=_("Allow open in place"),
        help=_("Show button for opening not-in-popup."),
        default=False,
        scope=Scope.settings,
    )
    weight = Float(default=1, scope=Scope.settings)
    lesson_score = Float(scope=Scope.user_state, default=0)
    _scorm_url = String(
        display_name=_("SCORM file URL"), default="", scope=Scope.settings,
    )
    _scorm_version = String(
        default=ScormVersions["SCORM_12"].value, scope=Scope.settings
    )
    # save completion_status for SCORM_2004
    _lesson_status = String(scope=Scope.user_state, default="not attempted")
    _success_status = String(scope=Scope.user_state, default="unknown")
    _scorm_data = Dict(scope=Scope.user_state, default={})

    def student_view(self, context={}):
        # TODO: We should be able to display an error message
        # instead of trying to render an inexistent or problematic
        # SCORM package
        try:
            self._ensure_scorm_package_is_extracted()
        except ScormManifestNotFoundException as e:
            logger.error(e)
        except ScormPackageNotFoundException as e:
            logger.error(e)

        template = render_template(
            "static/html/scormxblock.html",
            {"completion_status": self._get_completion_status(), "scorm_xblock": self},
        )
        fragment = Fragment(template)
        fragment.add_css(resource_string("static/css/scormxblock.css"))
        fragment.add_javascript(resource_string("static/js/src/scormxblock.js"))
        js_settings = {
            "scorm_version": self._scorm_version,
            "scorm_url": self._scorm_url,
            "completion_status": self._get_completion_status(),
            "scorm_xblock": {
                "display_name": self.display_name,
                "width": self.width,
                "height": self.height,
                "popup": self.popup,
                "autoopen": self.autoopen,
                "allowopeninplace": self.allowopeninplace,
            },
        }
        fragment.initialize_js("ScormXBlock", json_args=js_settings)
        return fragment

    def studio_view(self, context={}):
        # TODO: We should be able to display an error message
        # instead of trying to render an inexistent or problematic
        # SCORM package
        try:
            self._ensure_scorm_package_is_extracted()
        except ScormManifestNotFoundException as e:
            logger.error(e)
        except ScormPackageNotFoundException as e:
            logger.error(e)

        template = render_template(
            "static/html/studio.html",
            {
                "display_name_field": self.fields["display_name"],
                "scorm_file_field": self.fields["scorm_file"],
                "scorm_index_field": self.fields["scorm_index"],
                "has_score_field": self.fields["has_score"],
                "icon_class_field": self.fields["icon_class"],
                "width_field": self.fields["width"],
                "height_field": self.fields["height"],
                "popup_field": self.fields["popup"],
                "autoopen_field": self.fields["autoopen"],
                "allowopeninplace_field": self.fields["allowopeninplace"],
                "scorm_xblock": self,
            },
        )
        fragment = Fragment(template)
        fragment.add_css(resource_string("static/css/scormxblock.css"))
        fragment.add_javascript(resource_string("static/js/src/studio.js"))
        fragment.initialize_js("ScormStudioXBlock")
        return fragment

    @XBlock.handler
    def studio_submit(self, request, suffix=""):
        """
        This function handles the Studio submit AJAX call.
        It must return a WebOb Response object as specified by the XBlock API
        specifications.
        https://edx.readthedocs.io/projects/xblock/en/latest/xblock.html#xblock.core.XBlock.handler
        """
        self.display_name = request.params.get("display_name")
        self.width = request.params.get("width")
        self.height = request.params.get("height")
        self.has_score = request.params.get("has_score")
        self.popup = request.params.get("popup")
        self.autoopen = request.params.get("autoopen")
        self.allowopeninplace = request.params.get("allowopeninplace")
        self.icon_class = request.params.get("icon_class")
        self.scorm_index = request.params.get("scorm_index") or ""
        self.scorm_file = request.params.get("scorm_file")

        try:
            self._save_scorm_package()
        except ScormManifestNotFoundException:
            return Response(
                json.dumps({"field": "scorm_file", "message": "Invalid SCORM file"}),
                content_type="application/json",
                status=400,
            )
        except ScormPackageNotFoundException:
            return Response(
                json.dumps(
                    {"field": "scorm_file", "message": "SCORM package not found"}
                ),
                content_type="application/json",
                status=404,
            )

        return Response(
            json.dumps({"message": "XBlock saved successfully !"}),
            content_type="application/json",
            status=200,
        )

    @XBlock.json_handler
    def scorm_get_value(self, data, suffix=""):
        name = data.get("name")
        if name in ["cmi.core._lesson_status", "cmi.completion_status"]:
            return {"value": self._lesson_status}
        elif name == "cmi.success_status":
            return {"value": self._success_status}
        elif name in ["cmi.core.score.raw", "cmi.score.raw"]:
            return {"value": self.lesson_score * 100}
        else:
            return {"value": self._scorm_data.get(name, "")}

    @XBlock.json_handler
    def scorm_set_value(self, data, suffix=""):
        payload = {"result": "success"}
        name = data.get("name")

        if name in ["cmi.core.lesson_status", "cmi.completion_status"]:
            self._lesson_status = data.get("value")
            if self.has_score and data.get("value") in [
                "completed",
                "failed",
                "passed",
            ]:
                self._publish_grade()
                payload.update({"lesson_score": self.lesson_score})
        elif name == "cmi.success_status":
            self._success_status = data.get("value")
            if self.has_score:
                if self._success_status == "unknown":
                    self.lesson_score = 0
                self._publish_grade()
                payload.update({"lesson_score": self.lesson_score})
        elif name in ["cmi.core.score.raw", "cmi.score.raw"] and self.has_score:
            self.lesson_score = int(data.get("value", 0)) / 100.0
            self._publish_grade()
            payload.update({"lesson_score": self.lesson_score})
        else:
            self._scorm_data[name] = data.get("value", "")

        payload.update({"completion_status": self._get_completion_status()})
        return payload

    def _publish_grade(self):
        if self._lesson_status == "failed" or (
            ScormVersions(self._scorm_version) > ScormVersions["SCORM_12"]
            and self._success_status in ["failed", "unknown"]
        ):
            self.runtime.publish(self, "grade", {"value": 0, "max_value": self.weight})
        else:
            self.runtime.publish(
                self, "grade", {"value": self.lesson_score, "max_value": self.weight}
            )

    def _get_completion_status(self):
        completion_status = self._lesson_status
        if (
            ScormVersions(self._scorm_version) > ScormVersions["SCORM_12"]
            and self._success_status != "unknown"
        ):
            completion_status = self._success_status
        return completion_status

    def _read_scorm_manifest(self, scorm_path):
        manifest_path = os.path.join(scorm_path, "imsmanifest.xml")
        try:
            return default_storage.open(manifest_path).read()
        except IOError:
            raise ScormManifestNotFoundException()

    def _update_scorm_url(self, scorm_md5):
        # We can't load the scorm file directly from the default_storage URL
        # since it will be blocked by the SAMEORIGIN policy
        self._scorm_url = reverse(
            "abstract_scorm_xblock:scorm_serve",
            kwargs={"md5": scorm_md5, "path": self.scorm_index},
        )

    def _update_scorm_index(self, manifest):
        if not self.scorm_index:
            try:
                self.scorm_index = (
                    etree.fromstring(manifest).find(".//{*}resource").get("href")
                )
            except (IOError, AttributeError):
                self.scorm_index = "index.html"

    def _update_scorm_version(self, manifest):
        try:
            self._scorm_version = (
                etree.fromstring(manifest).find(".//{*}schemaversion").text
            )
        except (IOError, AttributeError):
            self._scorm_version = ScormVersions["SCORM_12"].value

    def _search_scorm_package(self):
        scorm_content, count = contentstore().get_all_content_for_course(
            self.course_id,
            filter_params={
                "contentType": "application/zip",
                "displayname": self.scorm_file,
            },
        )
        if not count:
            raise ScormPackageNotFoundException()
        # Since course content names are unique we are sure that we
        # can't have multiple results, so we just pop the first.
        return scorm_content.pop()

    def _extract_scorm_package(self, scorm_package):
        """
        Extracts the SCORM package to the default storage if needed
        """
        scorm_path = os.path.join(settings.STORAGE_SCORM_PATH, scorm_package["md5"])
        if not default_storage.exists(scorm_path):
            # We are actually loading the whole zipfile in memory.
            # This step should probably be handled more carefully.
            scorm_zipfile_data = contentstore().find(scorm_package["asset_key"]).data
            with ZipFile(io.BytesIO(scorm_zipfile_data)) as zipfile_obj:
                # We can't save extracted files directly
                # ZipFile does not provide a seek method till python 3.7
                # https://bugs.python.org/issue22908
                for filename in zipfile_obj.namelist():
                    default_storage.save(
                        os.path.join(
                            settings.STORAGE_SCORM_PATH, scorm_package["md5"], filename
                        ),
                        io.BytesIO(zipfile_obj.read(filename)),
                    )
        return scorm_path

    def _ensure_scorm_package_is_extracted(self):
        scorm_package = self._search_scorm_package()
        scorm_path = self._extract_scorm_package(scorm_package)
        return scorm_package, scorm_path

    def _save_scorm_package(self):
        if self.scorm_file:
            scorm_package, scorm_path = self._ensure_scorm_package_is_extracted()
            manifest = self._read_scorm_manifest(scorm_path)
            self._update_scorm_version(manifest)
            self._update_scorm_index(manifest)
            self._update_scorm_url(scorm_package["md5"])
        else:
            self._scorm_url = ""
            self._scorm_version = ""

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "AbstractScormXBlock",
                """<vertical_demo>
                <abstract_scorm_xblock/>
                </vertical_demo>
            """,
            ),
        ]

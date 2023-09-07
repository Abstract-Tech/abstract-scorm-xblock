# -*- coding: utf-8 -*-
import os
import io
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
from xblock.completable import CompletableXBlockMixin

from .utils import gettext as _
from .utils import resource_string, render_template
from .constants import ScormVersions
from .exceptions import ScormManifestNotFoundException, ScormPackageNotFoundException


logger = logging.getLogger(__name__)


class AbstractScormXBlock(XBlock, CompletableXBlockMixin):
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
    weight = Float(scope=Scope.settings, default=1)
    lesson_score = Float(scope=Scope.user_state, default=0)
    _scorm_url = String(scope=Scope.settings, default="")
    _scorm_version = String(
        scope=Scope.settings, default=ScormVersions["SCORM_12"].value
    )
    # save completion_status for SCORM_2004
    _lesson_status = String(scope=Scope.user_state, default="not attempted")
    _success_status = String(scope=Scope.user_state, default="unknown")

    """
    Fields description from
    https://scorm.com/scorm-explained/technical-scorm/run-time/run-time-reference/ :

    * cmi.learner_id (long_identifier_type (SPM: 4000), RO) Identifies the learner on behalf of whom the SCO was launched
    * cmi.location (characterstring (SPM: 1000), RW) The learner's current location in the SCO
    * cmi.suspend_data (characterstring (SPM: 4000), RW) Provides space to store and retrieve data between learner sessions
    * cmi.completion_status (“completed”, “incomplete”, “not attempted”, “unknown”, RW) Indicates whether the learner has completed the SCO
    * cmi.completion_threshold (real(10,7) range (0..1), RO) Used to determine whether the SCO should be considered complete
    * cmi.success_status (“passed”, “failed”, “unknown”, RW) Indicates whether the learner has mastered the SCO
    * cmi.score.scaled (real (10,7) range (-1..1), RW) Number that reflects the performance of the learner
    * cmi.score.raw (real (10,7), RW) Number that reflects the performance of the learner relative to the range bounded by the values of min and max
    * cmi.score.min (real (10,7), RW) Minimum value in the range for the raw score
    * cmi.score.max (real (10,7), RW) Maximum value in the range for the raw score
    """
    _scorm_data = Dict(scope=Scope.user_state, default={})

    @property
    def lesson_score_display(self):
        if self.has_score and self.lesson_score == self.weight:
            return int(self.weight)
        return round(self.lesson_score, 2)

    def student_view(self, context={}):
        # TODO: We should be able to display an error message
        # instead of trying to render an inexistent or problematic
        # SCORM package
        try:
            self._ensure_scorm_package_is_extracted()
        except ScormManifestNotFoundException as e:
            logger.warning(e)
        except ScormPackageNotFoundException as e:
            logger.warning(e)

        template = render_template(
            "static/html/scormxblock.html",
            {"completion_status": self.get_lesson_status(), "scorm_xblock": self},
        )
        fragment = Fragment(template)
        fragment.add_css(resource_string("static/css/scormxblock.css"))
        fragment.add_javascript(resource_string("static/js/src/scormxblock.js"))
        js_settings = {
            "scorm_version": self._scorm_version,
            "scorm_url": self._scorm_url,
            "scorm_data": self._scorm_data,
            "completion_status": self.get_lesson_status(),
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
            logger.warning(e)
        except ScormPackageNotFoundException as e:
            logger.warning(e)

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
                json_body={"field": "scorm_file", "message": "Invalid SCORM file"},
                content_type="application/json",
                status=400,
            )
        except ScormPackageNotFoundException:
            return Response(
                json_body={"field": "scorm_file", "message": "SCORM package not found"},
                content_type="application/json",
                status=404,
            )

        return Response(
            json_body={"message": "XBlock saved successfully !"},
            content_type="application/json",
            status=200,
        )

    def get_current_user_attributes(self, attribute):
        user = self.runtime.service(self, "user").get_current_user()
        return user.opt_attrs.get(attribute)

    @XBlock.json_handler
    def scorm_get_value(self, data, suffix=""):
        name = data.get("name")
        if name in ["cmi.core.lesson_status", "cmi.completion_status"]:
            return {"value": self._lesson_status}
        elif name == "cmi.success_status":
            return {"value": self._success_status}
        elif name in ["cmi.core.score.raw", "cmi.score.raw", "cmi.score.scaled"]:
            return {"value": self.lesson_score * 100}
        elif name in ["cmi.core.student_id", "cmi.learner_id"]:
            return {"value": self.get_current_user_attributes("edx-platform.user_id")}
        elif name in ["cmi.core.student_name", "cmi.learner_name"]:
            return {"value": self.get_current_user_attributes("edx-platform.username")}
        else:
            return {"value": self._scorm_data.get(name, "")}

    def get_payload(
        self,
        lesson_score,
        lesson_status,
        success_status,
        completion_status,
    ):
        payload = {"result": "success"}
        if lesson_score:
            self.lesson_score = lesson_score
            if success_status in ["failed", "unknown"]:
                lesson_score = 0
            else:
                lesson_score = lesson_score * self.weight
            payload.update({"lesson_score": lesson_score})

        if lesson_status:
            self._lesson_status = lesson_status
            payload.update({"completion_status": lesson_status})

        if completion_status:
            self.completion_status = completion_status
            payload.update({"completion_status": completion_status})

        return payload

    @XBlock.json_handler
    def scorm_set_value(self, data, suffix=""):
        name = data.get("name")
        value = data.get("value")

        lesson_score = None
        lesson_status = None
        success_status = None
        completion_status = None
        completion_percent = None

        self._scorm_data[name] = value

        if name in ["cmi.core.lesson_status", "cmi.completion_status"]:
            lesson_status = value
            if lesson_status in ["passed", "failed"]:
                success_status = lesson_status
            elif lesson_status in ["completed", "incomplete"]:
                completion_status = lesson_status
        elif name == "cmi.success_status":
            success_status = value
        elif name == "cmi.completion_status":
            completion_status = value
        elif (
            name in ["cmi.core.score.raw", "cmi.score.raw", "cmi.score.scaled"]
            and self.has_score
        ):
            lesson_score = float(value) / 100
        elif name == "cmi.progress_measure":
            completion_percent = float(value)

        if completion_status == "completed":
            self.emit_completion(1)
        if completion_percent:
            self.emit_completion(completion_percent)

        if success_status or completion_status == "completed":
            if self.has_score:
                self._publish_grade()

        return self.get_payload(
            lesson_score,
            lesson_status,
            success_status,
            completion_status,
        )

    def set_score(self, score):
        """
        Utility method used to rescore a problem.
        """
        if self.has_score:
            self.lesson_score = score.raw_earned
            self._publish_grade()
            self.emit_completion(1)

    def _publish_grade(self):
        if self._lesson_status == "failed" or (
            self.scorm_file
            and ScormVersions(self._scorm_version) > ScormVersions["SCORM_12"]
            and self._success_status in ["failed", "unknown"]
        ):
            self.runtime.publish(self, "grade", {"value": 0, "max_value": self.weight})
        else:
            self.runtime.publish(
                self, "grade", {"value": self.lesson_score, "max_value": self.weight}
            )

    def get_lesson_status(self):
        lesson_status = self._lesson_status
        if (
            self.scorm_file
            and ScormVersions(self._scorm_version) > ScormVersions["SCORM_12"]
            and self._success_status != "unknown"
        ):
            lesson_status = self._success_status
        return lesson_status

    def _read_scorm_manifest(self, scorm_path):
        manifest_path = os.path.join(scorm_path, "imsmanifest.xml")
        try:
            return default_storage.open(manifest_path).read()
        except IOError:
            raise ScormManifestNotFoundException(
                'Scorm manifest "{}" not found'.format(manifest_path)
            )

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
            self.runtime.course_id,
            filter_params={"displayname": self.scorm_file},
        )
        zip_mimetypes = {"application/x-zip-compressed", "application/zip"}
        if not count or scorm_content[0]["contentType"] not in zip_mimetypes:
            raise ScormPackageNotFoundException(
                'SCORM package "{}" not found'.format(self.scorm_file)
            )
        # Since course content names are unique we are sure that we
        # can't have multiple results, so we just pop the first.
        return scorm_content.pop()

    def _extract_scorm_package(self, scorm_package):
        """
        Extracts the SCORM package to the default storage if needed
        """
        scorm_path = os.path.join(settings.STORAGE_SCORM_PATH, scorm_package["md5"])

        try:
            self._read_scorm_manifest(scorm_path)
        except ScormManifestNotFoundException:
            # We are actually loading the whole zipfile in memory.
            # This step should probably be handled more carefully.
            scorm_zipfile_data = contentstore().find(scorm_package["asset_key"]).data
            with ZipFile(io.BytesIO(scorm_zipfile_data)) as zipfile_obj:
                # We can't save extracted files directly
                # ZipFile does not provide a seek method till python 3.7
                # https://bugs.python.org/issue22908
                for filename in zipfile_obj.namelist():
                    if filename.endswith("/"):
                        continue
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

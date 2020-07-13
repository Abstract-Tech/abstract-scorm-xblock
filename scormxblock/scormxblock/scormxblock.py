import json
import hashlib
import re
import os
import io
import logging
import pkg_resources
import xml.etree.ElementTree as ET

from zipfile import ZipFile
from functools import partial
from webob import Response

from django.core.files.storage import default_storage
from django.template import Context, Template

from xmodule.contentstore.django import contentstore

from xblock.core import XBlock
from xblock.fields import Scope, String, Float, Boolean, Dict, Integer
from xblock.fragment import Fragment

from .utils import gettext as _


logger = logging.getLogger(__name__)


class ScormXBlock(XBlock):

    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default="Scorm",
        scope=Scope.settings,
    )
    scorm_file = String(
        display_name=_("SCORM file package"),
        help=_(
            'Studio URL of the SCORM Zip file uploaded through the "Files & Uploads" section of the Course'
        ),
        default="",
        scope=Scope.settings,
    )
    scorm_index_page = String(
        display_name=_("Path to the index page in scorm file"),
        scope=Scope.settings,
        default="index.html",
    )
    has_score = Boolean(
        display_name=_("Scored"),
        help=_(
            "Select False if this component will not receive a numerical score from the SCORM"
        ),
        default=True,
        scope=Scope.settings,
    )
    icon_class = String(default="video", scope=Scope.settings,)
    width = Integer(
        display_name=_("Display Width (px)"),
        help=_("Width of iframe, if empty, the default 100%"),
        scope=Scope.settings,
    )
    height = Integer(
        display_name=_("Display Height (px)"),
        help=_("Height of iframe"),
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
    _scorm_url = String(
        display_name=_("SCORM file URL"), default="", scope=Scope.settings,
    )
    _scorm_version = String(default="SCORM_12", scope=Scope.settings,)
    # save completion_status for SCORM_2004
    _lesson_status = String(scope=Scope.user_state, default="not attempted")
    _success_status = String(scope=Scope.user_state, default="unknown")
    _scorm_data = Dict(scope=Scope.user_state, default={})
    _lesson_score = Float(scope=Scope.user_state, default=0)

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        context_html = self.get_context_student()
        template = self.render_template("static/html/scormxblock.html", context_html)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/scormxblock.css"))
        frag.add_javascript(self.resource_string("static/js/src/scormxblock.js"))
        settings = {"scorm_version": self._scorm_version}
        settings.update(self.get_settings_student())
        frag.initialize_js("ScormXBlock", json_args=settings)
        return frag

    def studio_view(self, context=None):
        context_html = self.get_context_studio()
        template = self.render_template("static/html/studio.html", context_html)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/scormxblock.css"))
        frag.add_javascript(self.resource_string("static/js/src/studio.js"))
        frag.initialize_js("ScormStudioXBlock")
        return frag

    @XBlock.handler
    def studio_submit(self, request, suffix=""):
        """
        This function handles the Studio submit AJAX call.
        It must return a WebOb Response object as specified in the XBlock API
        specifications.
        https://edx.readthedocs.io/projects/xblock/en/latest/xblock.html#xblock.core.XBlock.handler
        """
        self.display_name = request.params.get("display_name")
        self.width = request.params["width"]
        self.height = request.params.get("height")
        self.has_score = request.params.get("has_score")
        self.popup = request.params.get("popup")
        self.autoopen = request.params.get("autoopen")
        self.allowopeninplace = request.params.get("allowopeninplace")
        self.icon_class = "problem" if self.has_score == "True" else "video"

        filename = request.params["scorm_file"].split("/").pop()

        if filename:
            content, count = contentstore().get_all_content_for_course(
                self.course_id,
                filter_params={"contentType": "application/zip", "filename": filename,},
            )
            if not count:
                return Response(
                    json.dumps({"field": "scorm_file", "message": "No zipfile found"}),
                    content_type="application/json",
                    status=404,
                )
            if count > 1:
                return Response(
                    json.dumps(
                        {"field": "scorm_file", "message": "Multiple zipfiles found"}
                    ),
                    content_type="application/json",
                    status=400,
                )
            if count == 1:
                # We are actually loading the whole zipfile in memory.
                # This step should probably be handled more carefully.
                scorm_zipfile_data = (
                    contentstore().find(content[0].get("asset_key")).data
                )
                with ZipFile(io.BytesIO(scorm_zipfile_data)) as zipfile_obj:
                    # We can't save extracted files directly
                    # ZipFile does not provide a seek method till python 3.7
                    # https://bugs.python.org/issue22908
                    for filename in zipfile_obj.namelist():
                        if filename == "imsmanifest.xml":
                            self.parse_manifest(io.BytesIO(zipfile_obj.read(filename)))
                        default_storage.save(
                            os.path.join("public", content[0].get("md5"), filename),
                            io.BytesIO(zipfile_obj.read(filename)),
                        )
                self.scorm_file = request.params["scorm_file"]
                # We can't load the scormfile directly from the default_storage URL
                # since it will be blocked by the SAMEORIGIN policy
                self._scorm_url = "/scormxblock/{}/{}".format(
                    content[0].get("md5"), self.scorm_index_page
                )
                return Response(
                    json.dumps({"message": "SCORM package uploaded successfully !"}),
                    content_type="application/json",
                    status=200,
                )
        return Response(
            json.dumps({"field": "scorm_file", "message": "Unhandled error"}),
            content_type="application/json",
            status=400,
        )

    @XBlock.json_handler
    def scorm_get_value(self, data, suffix=""):
        name = data.get("name")
        if name in ["cmi.core._lesson_status", "cmi.completion_status"]:
            return {"value": self._lesson_status}
        elif name == "cmi._success_status":
            return {"value": self._success_status}
        elif name in ["cmi.core.score.raw", "cmi.score.raw"]:
            return {"value": self._lesson_score * 100}
        else:
            return {"value": self._scorm_data.get(name, "")}

    @XBlock.json_handler
    def scorm_set_value(self, data, suffix=""):
        context = {"result": "success"}
        name = data.get("name")

        if name in ["cmi.core._lesson_status", "cmi.completion_status"]:
            self._lesson_status = data.get("value")
            if self.has_score and data.get("value") in [
                "completed",
                "failed",
                "passed",
            ]:
                self.publish_grade()
                context.update({"_lesson_score": self._lesson_score})

        elif name == "cmi._success_status":
            self._success_status = data.get("value")
            if self.has_score:
                if self._success_status == "unknown":
                    self._lesson_score = 0
                self.publish_grade()
                context.update({"_lesson_score": self._lesson_score})
        elif name in ["cmi.core.score.raw", "cmi.score.raw"] and self.has_score:
            self._lesson_score = int(data.get("value", 0)) / 100.0
            self.publish_grade()
            context.update({"_lesson_score": self._lesson_score})
        else:
            self._scorm_data[name] = data.get("value", "")

        context.update({"completion_status": self.get_completion_status()})
        return context

    def publish_grade(self):
        if self._lesson_status == "failed" or (
            self._scorm_version == "SCORM_2004"
            and self._success_status in ["failed", "unknown"]
        ):
            self.runtime.publish(self, "grade", {"value": 0, "max_value": self.weight})
        else:
            self.runtime.publish(
                self, "grade", {"value": self._lesson_score, "max_value": self.weight}
            )

    def max_score(self):
        """
        Return the maximum score possible.
        """
        return self.weight if self.has_score else None

    def get_context_studio(self):
        return {
            "field_display_name": self.fields["display_name"],
            "field_scorm_file": self.fields["scorm_file"],
            "field_has_score": self.fields["has_score"],
            "field_width": self.fields["width"],
            "field_height": self.fields["height"],
            "popup": self.fields["popup"],
            "autoopen": self.fields["autoopen"],
            "allowopeninplace": self.fields["allowopeninplace"],
            "scorm_xblock": self,
        }

    def get_context_student(self):
        return {
            "scorm_file_path": self._scorm_url,
            "completion_status": self.get_completion_status(),
            "scorm_xblock": self,
        }

    def get_settings_student(self):
        return {
            "scorm_file_path": self._scorm_url,
            "completion_status": self.get_completion_status(),
            "scorm_xblock": {
                "display_name": self.display_name,
                "width": self.width,
                "height": self.height,
                "popup": self.popup,
                "autoopen": self.autoopen,
                "allowopeninplace": self.allowopeninplace,
            },
        }

    def render_template(self, template_path, context):
        template_str = self.resource_string(template_path)
        template = Template(template_str)
        return template.render(Context(context))

    def parse_manifest(self, manifest):
        try:
            tree = ET.parse(manifest)
        except IOError as e:
            logger.warning(e)
            return

        namespace = ""
        # Put back the offset to byte 0 since we already read this file.
        # Not sure we really need to instantiate another ET instance here.
        manifest.seek(0)
        for node in [node for _, node in ET.iterparse(manifest, events=["start-ns"])]:
            if node[0] == "":
                namespace = node[1]
                break

        root = tree.getroot()
        if namespace:
            resource = root.find("{{{0}}}resources/{{{0}}}resource".format(namespace))
            schemaversion = root.find(
                "{{{0}}}metadata/{{{0}}}schemaversion".format(namespace)
            )
        else:
            resource = root.find("resources/resource")
            schemaversion = root.find("metadata/schemaversion")

        if (schemaversion is not None) and (
            re.match("^1.2$", schemaversion.text) is None
        ):
            self._scorm_version = "SCORM_2004"
        else:
            self._scorm_version = "SCORM_12"

        self.scorm_index_page = "index.html"
        if resource:
            self.scorm_index_page = resource.get("href")

    def get_completion_status(self):
        completion_status = self._lesson_status
        if self._scorm_version == "SCORM_2004" and self._success_status != "unknown":
            completion_status = self._success_status
        return completion_status

    def _file_storage_path(self):
        """
        Get file path of storage.
        """
        path = (
            "{loc.org}/{loc.course}/{loc.block_type}/{loc.block_id}"
            "/{sha1}{ext}".format(
                loc=self.location,
                sha1=self.scorm_file_meta["sha1"],
                ext=os.path.splitext(self.scorm_file_meta["name"])[1],
            )
        )
        return path

    def get_sha1(self, file_descriptor):
        """
        Get file hex digest (fingerprint).
        """
        block_size = 8 * 1024
        sha1 = hashlib.sha1()
        for block in iter(partial(file_descriptor.read, block_size), ""):
            sha1.update(block)
        file_descriptor.seek(0)
        return sha1.hexdigest()

    def student_view_data(self):
        """
        Inform REST api clients about original file location and it's "freshness".
        Make sure to include `student_view_data=scormxblock` to URL params in the request.
        """
        if self.scorm_file and self.scorm_file_meta:
            return {
                "last_modified": self.scorm_file_meta.get("last_updated", ""),
                "scorm_data": default_storage.url(self._file_storage_path()),
                "size": self.scorm_file_meta.get("size", 0),
                "index_page": self.scorm_index_page,
            }
        return {}

    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            (
                "ScormXBlock",
                """<vertical_demo>
                <scormxblock/>
                </vertical_demo>
            """,
            ),
        ]

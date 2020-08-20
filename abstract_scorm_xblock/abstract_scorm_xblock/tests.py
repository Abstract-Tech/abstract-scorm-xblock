# -*- coding: utf-8 -*-
import json

import mock
import unittest

import ddt

from xblock.field_data import DictFieldData

from .constants import ScormVersions
from .scormxblock import AbstractScormXBlock


@ddt.ddt
class AbstractScormXBlockTests(unittest.TestCase):
    def make_one(self, **kwargs):
        """
        Creates a AbstractScormXBlock for testing purpose.
        """
        field_data = DictFieldData(kwargs)
        xblock = AbstractScormXBlock(mock.MagicMock(), field_data, mock.MagicMock())
        return xblock

    def test_fields_xblock(self):
        xblock = self.make_one()
        self.assertEqual(xblock.display_name, "SCORM unit")
        self.assertEqual(xblock.scorm_file, "")
        self.assertEqual(xblock.scorm_index, "")
        self.assertEqual(xblock.lesson_score, 0)
        self.assertEqual(xblock.has_score, True)
        self.assertEqual(xblock.icon_class, "problem")
        self.assertEqual(xblock.width, None)
        self.assertEqual(xblock.height, 450)
        self.assertEqual(xblock.popup, False)
        self.assertEqual(xblock.autoopen, False)
        self.assertEqual(xblock.allowopeninplace, False)
        self.assertEqual(xblock.weight, 1)
        self.assertEqual(xblock._scorm_version, ScormVersions["SCORM_12"].value)
        self.assertEqual(xblock._lesson_status, "not attempted")
        self.assertEqual(xblock._success_status, "unknown")

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.contentstore",
        return_value=mock.Mock(
            get_all_content_for_course=mock.Mock(return_value=[[], 0])
        ),
    )
    def test_student_view(self, contentstore):
        xblock = self.make_one()
        fragment = xblock.student_view()

        self.assertIn(xblock._lesson_status, fragment.body_html())
        self.assertIn(
            'lesson_score">{}</span>/{} points'.format(
                xblock.lesson_score, xblock.weight
            ),
            fragment.body_html(),
        )

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.contentstore",
        return_value=mock.Mock(
            get_all_content_for_course=mock.Mock(return_value=[[], 0])
        ),
    )
    def test_studio_view(self, contentstore):
        xblock = self.make_one()
        fragment = xblock.studio_view()

        self.assertIn(xblock.display_name, fragment.body_html())
        self.assertIn(str(xblock.height), fragment.body_html())
        self.assertIn("Save", fragment.body_html())
        self.assertIn("Cancel", fragment.body_html())

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.contentstore",
        return_value=mock.Mock(
            get_all_content_for_course=mock.Mock(return_value=[[], 0])
        ),
    )
    def test_studio_submit(self, contentstore):
        xblock = self.make_one()

        fields = {
            "display_name": "Test SCORM XBlock",
            "has_score": "True",
            "icon_class": "video",
            "height": 500,
        }

        response = xblock.studio_submit(mock.Mock(method="POST", params=fields))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(xblock.display_name, fields["display_name"])
        self.assertEqual(xblock.has_score, fields["has_score"])
        self.assertEqual(xblock.icon_class, "video")
        self.assertEqual(xblock.width, None)
        self.assertEqual(xblock.height, 500)
        self.assertEqual(xblock._scorm_version, "1.2")
        self.assertEqual(xblock._scorm_url, "")

        fields = {"scorm_file": "inexistent"}
        response = xblock.studio_submit(mock.Mock(method="POST", params=fields))
        self.assertEqual(response.status_code, 404)

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.AbstractScormXBlock._get_completion_status",
        return_value="completion_status",
    )
    @mock.patch("abstract_scorm_xblock.scormxblock.AbstractScormXBlock._publish_grade")
    @ddt.data(
        {"name": "cmi.core.lesson_status", "value": "completed"},
        {"name": "cmi.completion_status", "value": "failed"},
        {"name": "cmi.success_status", "value": "unknown"},
    )
    def test_set_status(self, value, _publish_grade, _get_completion_status):
        xblock = self.make_one(has_score=True)

        response = xblock.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _publish_grade.assert_called_once_with()
        _get_completion_status.assert_called_once_with()

        if value["name"] == "cmi.success_status":
            self.assertEqual(xblock._success_status, value["value"])
        else:
            self.assertEqual(xblock._lesson_status, value["value"])

        self.assertEqual(
            response.json,
            {
                "completion_status": "completion_status",
                "lesson_score": 0,
                "result": "success",
            },
        )

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.AbstractScormXBlock._get_completion_status",
        return_value="completion_status",
    )
    @ddt.data(
        {"name": "cmi.core.score.raw", "value": "20"},
        {"name": "cmi.score.raw", "value": "20"},
    )
    def test_set_lesson_score(self, value, _get_completion_status):
        xblock = self.make_one(has_score=True)

        response = xblock.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _get_completion_status.assert_called_once_with()

        self.assertEqual(xblock.lesson_score, 0.2)

        self.assertEqual(
            response.json,
            {
                "completion_status": "completion_status",
                "lesson_score": 0.2,
                "result": "success",
            },
        )

    @mock.patch(
        "abstract_scorm_xblock.scormxblock.AbstractScormXBlock._get_completion_status",
        return_value="completion_status",
    )
    @ddt.data(
        {"name": "cmi.core.lesson_location", "value": 1},
        {"name": "cmi.location", "value": 2},
        {"name": "cmi.suspend_data", "value": [1, 2]},
    )
    def test_set_other_scorm_values(self, value, _get_completion_status):
        xblock = self.make_one(has_score=True)

        response = xblock.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _get_completion_status.assert_called_once()

        self.assertEqual(xblock._scorm_data[value["name"]], value["value"])

        self.assertEqual(
            response.json,
            {"completion_status": "completion_status", "result": "success"},
        )

    @ddt.data(
        {"name": "cmi.core.lesson_status"},
        {"name": "cmi.completion_status"},
        {"name": "cmi.success_status"},
    )
    def test_scorm_get_status(self, value):
        xblock = self.make_one(_lesson_status="status", _success_status="status")

        response = xblock.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": "status"})

    @ddt.data(
        {"name": "cmi.core.score.raw"}, {"name": "cmi.score.raw"},
    )
    def test_scorm_get_lesson_score(self, value):
        xblock = self.make_one(lesson_score=0.2)

        response = xblock.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": 20})

    @ddt.data(
        {"name": "cmi.core.lesson_location"},
        {"name": "cmi.location"},
        {"name": "cmi.suspend_data"},
    )
    def test_get_other_scorm_values(self, value):
        xblock = self.make_one(
            _scorm_data={
                "cmi.core.lesson_location": 1,
                "cmi.location": 2,
                "cmi.suspend_data": [1, 2],
            }
        )

        response = xblock.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": xblock._scorm_data[value["name"]]})

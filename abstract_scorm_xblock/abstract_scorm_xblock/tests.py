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
        block = AbstractScormXBlock(mock.Mock(), field_data, mock.Mock())
        block.location = mock.Mock(
            block_id="block_id", org="org", course="course", block_type="block_type"
        )
        return block

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

    def test_save_settings_scorm(self):
        xblock = self.make_one()

        fields = {
            "display_name": "Test SCORM XBlock",
            "has_score": "True",
            "icon_class": "video",
            "scorm_file": "",
            "width": 800,
            "height": 450,
        }

        xblock.studio_submit(mock.Mock(method="POST", params=fields))
        self.assertEqual(xblock.display_name, fields["display_name"])
        self.assertEqual(xblock.has_score, fields["has_score"])
        self.assertEqual(xblock.icon_class, "video")
        self.assertEqual(xblock.width, 800)
        self.assertEqual(xblock.height, 450)

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
        block = self.make_one(has_score=True)

        response = block.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _publish_grade.assert_called_once_with()
        _get_completion_status.assert_called_once_with()

        if value["name"] == "cmi.success_status":
            self.assertEqual(block.success_status, value["value"])
        else:
            self.assertEqual(block._lesson_status, value["value"])

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
        block = self.make_one(has_score=True)

        response = block.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _get_completion_status.assert_called_once_with()

        self.assertEqual(block.lesson_score, 0.2)

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
        block = self.make_one(has_score=True)

        response = block.scorm_set_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        _get_completion_status.assert_called_once_with()

        self.assertEqual(block._scorm_data[value["name"]], value["value"])

        self.assertEqual(
            response.json,
            {"completion_status": "completion_status", "result": "success"},
        )

    @ddt.data(
        {"name": "cmi.core._lesson_status"},
        {"name": "cmi.completion_status"},
        {"name": "cmi._success_status"},
    )
    def test_scorm_get_status(self, value):
        block = self.make_one(_lesson_status="status", _success_status="status")

        response = block.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": "status"})

    @ddt.data(
        {"name": "cmi.core.score.raw"}, {"name": "cmi.score.raw"},
    )
    def test_scorm_get_lesson_score(self, value):
        block = self.make_one(lesson_score=0.2)

        response = block.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": 20})

    @ddt.data(
        {"name": "cmi.core.lesson_location"},
        {"name": "cmi.location"},
        {"name": "cmi.suspend_data"},
    )
    def test_get_other_scorm_values(self, value):
        block = self.make_one(
            _scorm_data={
                "cmi.core.lesson_location": 1,
                "cmi.location": 2,
                "cmi.suspend_data": [1, 2],
            }
        )

        response = block.scorm_get_value(
            mock.Mock(method="POST", body=json.dumps(value))
        )

        self.assertEqual(response.json, {"value": block._scorm_data[value["name"]]})

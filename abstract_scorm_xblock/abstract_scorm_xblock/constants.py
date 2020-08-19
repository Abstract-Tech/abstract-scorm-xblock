# -*- coding: utf-8 -*-
from enum import Enum


ORDERED_VERSIONS = [
    "SCORM_12",
    "SCORM_2004_2_EDITION",
    "SCORM_2004_3_EDITION",
    "SCORM_2004_4_EDITION",
]


class ScormVersions(Enum):
    """
    List SCORM versions which can be found in supported manifest templates.
    Reference templates can be found at https://scorm.com/scorm-explained/technical-scorm/content-packaging/xml-schema-definition-files/
    """

    SCORM_12 = "1.2"
    SCORM_2004_2_EDITION = "CAM 1.3"
    SCORM_2004_3_EDITION = "2004 3rd Edition"
    SCORM_2004_4_EDITION = "2004 4th Edition"

    def __lt__(self, other):
        assert isinstance(other, self.__class__)
        return ORDERED_VERSIONS.index(self.name) < ORDERED_VERSIONS.index(other.name)

    def __gt__(self, other):
        assert isinstance(other, self.__class__)
        return ORDERED_VERSIONS.index(self.name) > ORDERED_VERSIONS.index(other.name)

# -*- coding: utf-8 -*-
"""Setup for abstract_scorm_xblock XBlock."""

from setuptools import setup


setup(
    name="abstract_scorm_xblock",
    version="0.6",
    description="Load SCORM packages into Open edX courses",
    packages=["abstract_scorm_xblock"],
    install_requires=["XBlock"],
    tests_require=["freezegun==0.3.11"],
    entry_points={
        "xblock.v1": [
            "abstract_scorm_xblock = abstract_scorm_xblock.scormxblock:AbstractScormXBlock"
        ],
        "lms.djangoapp": [
            "abstract_scorm_xblock = abstract_scorm_xblock.app:AbstractScormXBlockAppConfig"
        ],
        "cms.djangoapp": [
            "abstract_scorm_xblock = abstract_scorm_xblock.app:AbstractScormXBlockAppConfig"
        ],
    },
    include_package_data=True,
    license="Apache",
    classifiers=["License :: OSI Approved :: Apache Software License"],
)

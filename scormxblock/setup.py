# -*- coding: utf-8 -*-
"""Setup for scormxblock XBlock."""

from setuptools import setup


setup(
    name="scormxblock-xblock",
    version="0.5",
    description="Load SCORM packages into Open edX courses",
    packages=["scormxblock"],
    install_requires=["XBlock", "freezegun==0.3.11"],
    entry_points={"xblock.v1": ["scormxblock = scormxblock:ScormXBlock"]},
    include_package_data=True,
    license="Apache",
    classifiers=["License :: OSI Approved :: Apache Software License"],
)

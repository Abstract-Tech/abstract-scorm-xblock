"""Setup for scormxblock XBlock."""

import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name="scormxblock-xblock",
    version="0.5",
    description="Load SCORM packages into Open edX courses",
    packages=["scormxblock"],
    install_requires=["XBlock", "freezegun==0.3.11"],
    entry_points={"xblock.v1": ["scormxblock = scormxblock:ScormXBlock"]},
    package_data=package_data("scormxblock", ["static", "public", "locale"]),
    license="Apache",
    classifiers=["License :: OSI Approved :: Apache Software License"],
)

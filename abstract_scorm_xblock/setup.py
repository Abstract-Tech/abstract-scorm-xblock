# -*- coding: utf-8 -*-
"""Setup for abstract_scorm_xblock XBlock."""

from setuptools import setup


with open("README.md") as readme_file:
    readme = readme_file.read()

setup(
    name="abstract_scorm_xblock",
    version="1.0",
    description="Load SCORM packages into Open edX courses",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=["abstract_scorm_xblock"],
    install_requires=["XBlock"],
    include_package_data=True,
    keywords = ['scorm', 'xblock']
    author="Chiruzzi Marco, Silvio Tomatis",
    author_email="chiruzzi.marco@gmail.com, silviot@gmail.com",
    url="https://github.com/Abstract-Tech/abstract-scorm-xblock",
    download_url="https://github.com/Abstract-Tech/abstract-scorm-xblock/archive/v1.0.tar.gz",
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
    ],
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
)

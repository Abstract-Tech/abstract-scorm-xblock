# -*- coding: utf-8 -*-
"""Setup for abstract_scorm_xblock XBlock."""

import io
from setuptools import setup

with io.open("README.md", encoding="utf-8") as readme_file:
    readme = readme_file.read()

setup(
    name="abstract-scorm-xblock",
    version="1.0.0",
    description="Load SCORM packages into Open edX courses",
    long_description=readme,
    long_description_content_type="text/markdown",
    packages=["abstract_scorm_xblock"],
    install_requires=["XBlock"],
    include_package_data=True,
    keywords=["scorm", "xblock"],
    author="Alexander Marenich, Andrey Kryachko, Andrey Lykhoman, COTOHA, David Baumgold, Volodymyr Bergman, Maxim Starodubcev, Jorge Mora, Silvio Tomatis, kirkerafael, Oksana Slusarenro, Chiruzzi Marco",
    author_email="sendr84@gmail.com, andrey.kryachko@raccoongang.com, andrey.likhoman@gmail.com, sergiy.movchan@gmail.com, david@davidbaumgold.com, wowkalucky@gmail.com, starodubcevmax@gmail.com, jorge.mora@innovapues.com, silviot@gmail.com, kirkerafael@gmail.com, oksana.slu@gmail.com, chiruzzi.marco@gmail.com",
    maintainer="Silvio Tomatis, Chiruzzi Marco",
    maintainer_email="silviot@gmail.com, chiruzzi.marco@gmail.com",
    url="https://github.com/Abstract-Tech/abstract-scorm-xblock",
    download_url="https://github.com/Abstract-Tech/abstract-scorm-xblock/archive/v1.0.0.tar.gz",
    license="Apache 2.0",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Framework :: Django",
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

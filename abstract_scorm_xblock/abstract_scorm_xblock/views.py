# -*- coding: utf-8 -*-
import mimetypes
import os
import posixpath

from django.conf import settings
from django.http import FileResponse, Http404

from django.utils.http import http_date
from django.utils.six.moves.urllib.parse import unquote
from django.core.files.storage import default_storage
from django.conf.urls import url


def scormxblock_serve(request, md5, path):
    """
    Proxy files from the Django default storage in order to avoid SAMEORIGIN issues.
    """
    path = posixpath.normpath(unquote(path)).lstrip("/")
    fullpath = os.path.join(settings.STORAGE_SCORM_PATH, md5, path)

    if not default_storage.exists(fullpath):
        raise Http404()

    content_type, encoding = mimetypes.guess_type(fullpath)
    content_type = content_type or "application/octet-stream"
    response_file = default_storage.open(fullpath)
    response = FileResponse(response_file, content_type=content_type)
    response["Last-Modified"] = http_date(
        default_storage.get_modified_time(fullpath).toordinal()
    )
    response["Content-Length"] = response_file.size
    if encoding:
        response["Content-Encoding"] = encoding
    return response


urlpatterns = [
    url(r"(?P<md5>[a-f0-9]{32})/(?P<path>.*)$", scormxblock_serve, name="scorm_serve")
]

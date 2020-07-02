THIS FORK HAS:
===
* merged branch with opening SCORM in popup
* plenty of popup options (open at start, show "open inline" button)
* isolated APIs for multiple xblocks - you can have more than one SCORM package in one vertical, and scores are calculated as they should

THIS FORK STILL DOESN'T HAVE:
===
* proper deleting zip & unzipped content on ~~package replacing and~~ xblock deletion
* localization working as it should

edx_xblock_scorm
=========================
XBlock to display SCORM content within the Open edX LMS.  Editable within Open edx Studio. Will save student state and report scores to the progress tab of the course.
Currently supports SCORM 1.2 and SCORM 2004 standard.

Block displays SCORM which saved as `File -> Export -> Web Site -> Zip File`

Block displays SCORM which saved as `File -> Export -> SCORM 1.2`


Installation
------------

Install package

    pip install -e git+https://github.com/raccoongang/edx_xblock_scorm.git#egg=edx_xblock_scorm

Note: for OpenEdx releases prior ginkgo add required variables to CMS configuration ```<edx-platform-path>/cms/envs/aws.py```:

```
MEDIA_ROOT = ENV_TOKENS.get('MEDIA_ROOT', '/edx/var/edxapp/media/')
MEDIA_URL = ENV_TOKENS.get('MEDIA_URL', '/media/')
```

# Usage
* Add `scormxblock` to the list of advanced modules in the advanced settings of a course.
* Add a `scorm` component to your Unit.
* Upload a zip file containint your content package.  The `imsmanifest.xml` file must be at the root of the zipped package (i.e., make sure you don't have an additional directory at the root of the Zip archive which can handle if e.g., you select an entire folder and use Mac OS X's compress feature).
* Publish your content as usual.

Testing
-------

Assuming `scormxblock` is installed as above, you can run tests like so:

    $ python manage.py lms test scormxblock --keepdb

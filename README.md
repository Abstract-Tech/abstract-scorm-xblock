# THIS FORK HAS:

- merged branch with opening SCORM in popup
- plenty of popup options (open at start, show "open inline" button)
- isolated APIs for multiple xblocks - you can have more than one SCORM package in one vertical, and scores are calculated as they should

# THIS FORK STILL DOESN'T HAVE:

- proper deleting zip & unzipped content on ~~package replacing and~~ xblock deletion
- localization working as it should

# edx_xblock_scorm

XBlock to display SCORM content within the Open edX LMS. Editable within Open edx Studio. Will save student state and report scores to the progress tab of the course.
Currently supports SCORM 1.2 and SCORM 2004 standard.

Block displays SCORM which saved as `File -> Export -> Web Site -> Zip File`
Block displays SCORM which saved as `File -> Export -> SCORM 1.2`

## Installation

Install package

    pip install -e git+https://github.com/Abstract-Tech/edx_xblock_scorm.git#egg=edx_xblock_scorm&subdirectory=scormxblock

**WARNING: This package have to be installed using the `subdirectory` option.**

## Usage

- Add `scormxblock` to the list of advanced modules in the advanced settings of a course.
- Add a `scorm` component to your Unit.
- Upload a zip file containing your content package. **The `imsmanifest.xml` file must be at the root of the zipped package. Make sure you don't have an additional directory at the root of the Zip archive.**
- Publish your content as usual.

## Development

### Setup

To setup the development environment:

- create a Python3 virtualenv. If direnv is installed a `direnv allow` should be enough.
- install derex with `pip install -r requirements.txt`
- setup the derex project. Read https://derex.page/quickstart.html#quickstart for further informations.

### Running tests

Tests can be run from the derex project directory by running:

    `ddc-project run --rm lms python manage.py lms test scormxblock --keepdb`

The first time this command is run it will initialize the test database. Remove the `--keepdb` flag if you want the test database to be created/destroyed each time.

# Abstract Scorm XBlock

Yet another SCORM XBlock for Open edX®.

Supports course export/import. Editable within Open edx Studio. Saves student state and reports scores to the progress tab of the course.
Currently supports SCORM 1.2 and SCORM 2004 standards.

Developed by [Abstract Technology](https://abstract-technology.de/), based on [edx_xblock_scorm](https://github.com/raccoongang/edx_xblock_scorm/) by [Raccoon Gang
](https://raccoongang.com/).

## Installation

Install package with

```shell
pip install abstract-scorm-xblock
```

## Usage

- Add `abstract_scorm_xblock` to the list of advanced modules in the advanced settings of a course.
- Add a `scorm` component to your Unit.
- Upload a zip file containing your content package. **The `imsmanifest.xml` file must be at the root of the zipped package. Make sure you don't have an additional directory at the root of the zip archive.**
- Publish your content as usual.

## Development

### Setup

To setup the development environment:

- create a Python3 virtualenv. If direnv is installed a `direnv allow` should be enough.
- install derex with `pip install -r requirements.txt`
- setup the derex project. Read [the documentation](https://derex.page/quickstart.html#quickstart) for further informations.

### Development and Debugging

In order to be able to develop and debug effectively some steps may be taken:

- get a shell inside the container:

  ```shell
  cd derex_project
  ddc-project exec cms sh
  ```

- setup the package in editable mode. This will allow for testing changes without the need to reinstall the package:

  ```shell
  pip install -e /openedx/derex.requirements/abstract_scorm_xblock
  ```

- launch the Django debug server manually and bind it on port `81`:

  ```shell
  python manage.py cms runserver 0:81
  ```

- on your browser [https://studio.scorm.localhost:81](https://studio.scorm.localhost:81) should now be available. You should now be able to insert debug code in both Python and JS files and benefit from Django runserver auto reload feature.

### Running tests

Tests can be run from the derex project directory by running:

```shell
ddc-project run --rm lms python manage.py lms test abstract_scorm_xblock --keepdb
```

The first time this command is run it will initialize the test database. Remove the `--keepdb` flag if you want the test database to be created/destroyed each time.

## Caveats

- If a SCORM package is deleted from the course "Files & Uploads" section, the Import/Export functionality will export a course with a broken XBlock.

## TODO

- Delete extracted old SCORM packages from default storage

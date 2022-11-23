# Changelog

All notable changes to this project will be documented in this file.

## [unreleased]

### Bug Fixes

- Wait for logger thread to quit gracefully before closing segger channel ([#28](https://github.com/orhun/git-cliff/issues/28))
- Qsize() not available for macos x
- Pytest config and flake8 excludes
- Remove --dev option (default for poetry)
- Restrict markupsafe versions and cleanup docs
- Use coverage coonfig from pyproject.toml
- Point to pykiso-python-uds-alpha for PYPI
- Multiple yaml logging
- Hanging ci and rework mp aux and proxy pytest
- Virtual test fail
- Skip suite tests when setup fails
- Redefine jenkins resources & timeouts
- Correct AttributeError when setUpClass failed for junit report generation ([#120](https://github.com/orhun/git-cliff/issues/120))
- MarkupSafe
- Update pykitest example
- Step report ci issues([#134](https://github.com/orhun/git-cliff/issues/134))
- Replace dependabot to .github ([#133](https://github.com/orhun/git-cliff/issues/133))
- Readthedocs requirements
- Changelog only triggered on master
- Cleanup auxiliary properly by removing them from sys.modules ([#147](https://github.com/orhun/git-cliff/issues/147))
- Fix double Logging with --junit option
- Update logging initializer so that internal logs are always logged in file
- Handle case odx_file_path parameter is type of bool ([#158](https://github.com/orhun/git-cliff/issues/158))
- Step report problem with inspect module in python>=3.8 ([#160](https://github.com/orhun/git-cliff/issues/160))
- Pcan logs for macos
- Make sure the action is triggered correctly ([#187](https://github.com/orhun/git-cliff/issues/187))
- Wrong copyright license used in test file
- Add connector_required flag with value False ([#199](https://github.com/orhun/git-cliff/issues/199))

### Documentation

- Restructure docs ([#14](https://github.com/orhun/git-cliff/issues/14))
- Autogen changelog ([#15](https://github.com/orhun/git-cliff/issues/15))
- Add links for how to create an auxiliary and connector ([#17](https://github.com/orhun/git-cliff/issues/17))
- Change auto changelog tool ([#30](https://github.com/orhun/git-cliff/issues/30))
- Remove not maintained 'list of limitations' section
- Add section whats new ([#38](https://github.com/orhun/git-cliff/issues/38))
- Replace all occurences of pipenv with poetry
- Rework getting_started
- Add whats new for 0.17.0
- Make usage of TestSuite elements more visible
- Add quality goals
- Add tools section and remove tools from coverage
- Align dependencies in NOTICE.md ([#90](https://github.com/orhun/git-cliff/issues/90))
- Fix dead links and rework formatting ([#105](https://github.com/orhun/git-cliff/issues/105))
- Extend contribution parts with DoD hints ([#94](https://github.com/orhun/git-cliff/issues/94))

### Features

- Update to new release 0.15 ([#13](https://github.com/orhun/git-cliff/issues/13))
- Add uptime for pcan inside python-can
- Expose yaml and cli configuration to user test cases/suites
- Add uptime for pcan inside python-can
- [**breaking**] Restore yaml loader in config parser ([#31](https://github.com/orhun/git-cliff/issues/31))
- Raise an exception when auxiliary failed at instance creation ([#33](https://github.com/orhun/git-cliff/issues/33))
- Update to new release 0.16.0 ([#34](https://github.com/orhun/git-cliff/issues/34))
- Update to new release 0.17.0
- Make bus error warnings switchable for pcan
- Set up badges
- Multiple yaml in CLI
- Rework pcan trace configuration in connector
- Add pykiso to pytest tool ([#62](https://github.com/orhun/git-cliff/issues/62))
- Make the proxy agnostic of transitioning messages
- Create base class for test ([#61](https://github.com/orhun/git-cliff/issues/61))
- Make release 0.18.0 ([#72](https://github.com/orhun/git-cliff/issues/72))
- Add show tag script for test information analysis
- Detect test collection errors and abort execution
- Implement double threaded auxiliary interface ([#74](https://github.com/orhun/git-cliff/issues/74))
- Make DuT DT-aux capable ([#77](https://github.com/orhun/git-cliff/issues/77))
- Add a tester present sender to uds auxiliary ([#87](https://github.com/orhun/git-cliff/issues/87))
- ComAux ability to handle reception buffer ([#86](https://github.com/orhun/git-cliff/issues/86))
- Improve error reporting in test case execution ([#111](https://github.com/orhun/git-cliff/issues/111))
- Improve error reporting in test case execution ([#111](https://github.com/orhun/git-cliff/issues/111)) ([#91](https://github.com/orhun/git-cliff/issues/91))
- Adapt UDS auxiliary and server to the dt auxiliary interface ([#114](https://github.com/orhun/git-cliff/issues/114))
- Add dependabot to manage our fixed dependencies ([#121](https://github.com/orhun/git-cliff/issues/121))
- Add new logging strategy ([#122](https://github.com/orhun/git-cliff/issues/122))
- Step report ([#101](https://github.com/orhun/git-cliff/issues/101))
- Make release 0.19.0 ([#130](https://github.com/orhun/git-cliff/issues/130))
- Add start and stop uds tester present sender ([#131](https://github.com/orhun/git-cliff/issues/131))
- Add cc_serial connector ([#124](https://github.com/orhun/git-cliff/issues/124))
- Select test case with regex ([#146](https://github.com/orhun/git-cliff/issues/146))
- Write stderr to file when file logging is activated ([#159](https://github.com/orhun/git-cliff/issues/159))
- Ensure default behaviour when (suite case) id is 0 ([#177](https://github.com/orhun/git-cliff/issues/177))
- Process connector ([#165](https://github.com/orhun/git-cliff/issues/165))
- Add stepreport example ([#192](https://github.com/orhun/git-cliff/issues/192))
- Make release 0.20.0 ([#194](https://github.com/orhun/git-cliff/issues/194))

### Miscellaneous Tasks

- Fix issues induced by tmp_path fixture
- Fix docstring
- Rename show-tag CLI to pykiso-tags
- Bump lxml from 4.9.0 to 4.9.1 ([#88](https://github.com/orhun/git-cliff/issues/88))
- Bump pre-commit from 2.19.0 to 2.20.0
- Bump coverage from 5.5 to 6.4.4
- Bump pytest-mock from 3.7.0 to 3.8.2
- Update changelog to newest version
- Update changelog to newest version
- Bump pylink-square from 0.12.0 to 0.14.2 ([#137](https://github.com/orhun/git-cliff/issues/137))
- Update changelog to newest version
- Update click ([#143](https://github.com/orhun/git-cliff/issues/143))
- Update changelog to newest version
- Release 0.19.1 ([#144](https://github.com/orhun/git-cliff/issues/144))
- Update changelog to newest version
- Add jinja2 for step reporter dependency
- Update changelog to newest version
- Update changelog to newest version
- [**breaking**] Release 0.19.2
- Update changelog to newest version
- Release 0.19.3 ([#161](https://github.com/orhun/git-cliff/issues/161))
- Update changelog to newest version
- Update changelog to newest version
- Bump pykiso-python-uds from 3.0.0 to 3.0.1 ([#163](https://github.com/orhun/git-cliff/issues/163))
- Bump pytest from 7.1.2 to 7.1.3 ([#155](https://github.com/orhun/git-cliff/issues/155))
- Debian:11.0
- Bump black from 22.3.0 to 22.8.0 ([#154](https://github.com/orhun/git-cliff/issues/154))
- Update changelog to newest version
- Bump invoke from 1.7.1 to 1.7.3
- Bump pylink-square from 0.14.2 to 0.14.3
- Bump black from 22.8.0 to 22.10.0 ([#179](https://github.com/orhun/git-cliff/issues/179))
- Update changelog to newest version
- Bump coverage from 6.4.4 to 6.5.0 ([#181](https://github.com/orhun/git-cliff/issues/181))
- Bump pytest-mock from 3.8.2 to 3.10.0 ([#178](https://github.com/orhun/git-cliff/issues/178))
- Bump tabulate from 0.8.10 to 0.9.0
- Bump pytest from 7.1.3 to 7.2.0
- Bump pytest-cov from 3.0.0 to 4.0.0
- Bump importlib-metadata from 4.12.0 to 5.0.0 ([#166](https://github.com/orhun/git-cliff/issues/166))
- Update changelog to newest version
- Update changelog to newest version

### Refactor

- [**breaking**] Change variant decorator
- [**breaking**] Change variant decorator
- Replace all setuptools-based files with poetry
- Migrate recorder to DT-aux interface ([#80](https://github.com/orhun/git-cliff/issues/80))
- Adapt acroname aux to dt interface ([#84](https://github.com/orhun/git-cliff/issues/84))
- Adapt instrument aux to dt interface ([#85](https://github.com/orhun/git-cliff/issues/85))
- Restructure the documentation
- Small fixes

### Testing

- Make test reliable ([#18](https://github.com/orhun/git-cliff/issues/18))
- Add missing unittests
- Add tests for show-tag
- Increase coverage
- Try to fix get_yaml_files test

### Bugfix

- Remove warning in unittests
- Remove warning in unittests
- Fix/adapt socketcan connectors to be agnostic ([#89](https://github.com/orhun/git-cliff/issues/89))
- Adapt rtt connector to create log folder if does not exist ([#92](https://github.com/orhun/git-cliff/issues/92))
- Do not wait for an UDS response in tester present sender ([#113](https://github.com/orhun/git-cliff/issues/113))

### Chor

- Pykiso python uds 3 0 0 ([#119](https://github.com/orhun/git-cliff/issues/119))

### Ci

- Github-action for codecov ([#27](https://github.com/orhun/git-cliff/issues/27))
- Add skip lock for pipenv to prevent hangup
- Add skip lock for pipenv to prevent hangup
- Update pipeline with poetry
- Skip poetry install
- Add poetry installation
- Replace auto-changelog

### Ci[dependabot]

- Update to monthly PRs ([#180](https://github.com/orhun/git-cliff/issues/180))

<!-- generated by git-cliff -->

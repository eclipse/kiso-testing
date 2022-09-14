Version 0.19.2
--------------

Filter for Test cases
^^^^^^^^^^^^^^^^^^^^^

It is now possible to select test classes or even test cases with a unix filename
pattern.
This pattern can be passed with the -p flag or inside the yaml file.

For more info see
:ref:`test_case_patterns`

BREAKING CHANGE - UdsAuxiliary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

UdsAuxiliary: odx_file_path now only supports None (not specified) or a valid path to a file

.. code:: yaml
    config:
        odx_file_path: ./valid/path/to/conf.odx
        # or
    config:
        odx_file_path: null
        # or
    config: null

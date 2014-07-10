innoslate-xml-parser
====================

Parses an Innoslate project's exported XML file, and creates custom CSV files from it.

Usage is simple: "python Innoslate_xml_parser innoslate_exported_file.xml"
Output files are written to the working directory, and will overwrite existing files.
Currently the following four files are output:
* Actions.csv
* Requirements.csv
* duplicate_actions.txt
* duplicate_requirements.txt

The script was initially written for Python 3.x, but since changed to run with Python 2.x instead.

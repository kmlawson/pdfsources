# anystyle-cli Notes

## Overview

The `anystyle-cli` is a command-line tool for finding and parsing bibliographic references within text documents or PDFs. It can extract references it finds and parse them from a list of one reference per line, converting them into structured formats.

## Key Features

*   **Find and Parse:** It can both find references in a document and parse them into structured data.
*   **Multiple Output Formats:** Supports various output formats, including BibTeX, CSL/JSON, and XML.
*   **Two Main Commands:**
    *   `find`: Discovers and extracts references from documents.
    *   `parse`: Segments and converts references into structured data.
*   **Custom Models:** Includes a `train` command to create custom finder or parser models.
*   **Validation:** Offers a `check` command to validate tagged training data.
*   **PDF Processing:** Relies on the `pdftotext` utility for PDF processing, which needs to be installed separately.

## Source

*   [inukshuk/anystyle-cli on GitHub](https://github.com/inukshuk/anystyle-cli)

# rad_nlp_anonymizer

## Overview
Anonymization tool for radiology reports and other medical texts. Anonymizes sensitive information (names, emails, dates, and Finnish social security numbers).

e.g. 
*"Vertailussa 1.1.2020 otetut kuvat. Rintarangassa näkyy osteoporoottinen kompressiomurtuma. Sitä ei näkynyt vielä 1/2020 kuvassa. Matti Meikäläinen, rad.el."*

-->
*"Vertailussa \*DATE\* otetut kuvat. Rintarangassa näkyy osteoporoottinen kompressiomurtuma. Sitä ei näkynyt vielä \*DATE\* kuvassa. \*NAME\*, rad.el."*


Based on the anonymization tool implementation in: https://medium.com/@mithilesh007/a-simple-way-to-anonymize-texts-locally-safeguard-finnish-phi-with-this-tool-d8e9adf97e38



## Features
- Anonymizes names, email addresses, dates, and Finnish social security numbers.
- Supports input and output text files, SQLite databases, and Excel (.xlsx) files (via openpyxl).

## Project structure
- `main.py` — entry point for running the anonymization flow.
- `excel_processing.py` — Excel-specific code for reading and writing `.xlsx` workbooks.
- `db_processing.py` — SQLite-specific code for selecting and updating rows in a database.
- `text_anonymization_tool.py` — the NLP and redaction logic.
- `utils.py` — model and environment helper functions.

## Requirements
- Python 3.11+
- PyTorch 2.5+
- Dependencies listed in `environment.yml`
- openpyxl (for Excel .xlsx support). Install with: `pip install openpyxl`

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/tnissinen/custom-text-anonymization-tool.git
    cd custom-text-anonymization-tool
    ```

2. Create and activate the conda environment:
    ```sh
    conda env create -f environment.yml
    conda activate rad_nlp_anonymizer
    ```
   
For GPU support, you can install PyTorch and torchvision with the following commands (select the appropriate CUDA version for your system, check https://pytorch.org/):

```sh
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130
```
   
## Usage (SQLite db and Excel)

### SQLite

1. Prepare your SQLite database with the appropriate schema.
2. Configure database table names etc. in `config.json`.
3. `main.py` calls the SQLite logic from `db_processing.py` automatically.
4. Run the main script:
    ```sh
    python main.py
    ```

### Excel (.xlsx)

1. Enable Excel processing in `config.json`:
   - set `use_excel` to `true`
   - set `excel_path` to the path of your `.xlsx` file
2. Ensure the first row of the Excel file contains header names and that `input_column` matches a header.
3. The script will add `output_column`, `score_column`, and `info_column` if they are missing and overwrite the original Excel file by default.
4. `main.py` routes Excel processing to `excel_processing.py`.
5. Run the main script:
   ```sh
   python main.py
   ```

## Configuration

The tool reads settings from config.json. Short explanations of the parameters:

- use_excel: true/false — enable Excel processing.
- excel_path: Path to the Excel file to process.
- db_path: Path to the SQLite database file.
- table_name: Name of the table containing reports.
- id_column: Column used as the row identifier (primary key).
- input_column: Column containing the original text to anonymize.
- output_column: Column where anonymized text will be written.
- score_column: Column to store anonymization score (number of words redacted).
- info_column: Column to store extra anonymization info or tags.
- printing: true/false — print progress and debug info to console.
- simple_tags: true/false — use simple replacement tags instead of verbose info.
- min_id / max_id: Integer range (inclusive) of id_column values to process.
- ignore_words: Array of words to skip during anonymization.
- names_to_anonymize: Array of specific names to anonymize.

Adjust these values in config.json before running the scripts.


## Usage (text files)

1. Place your input text file in the appropriate directory:
    ```plaintext
    base_path + "input_output_text_files/your_input_file.txt"
    ```

2. Run the text anonymization script:
    ```sh
    python text_anonymization_tool.py
    ```

3. The redacted output will be saved in the specified output directory:
    ```plaintext
    base_path + "input_output_text_files/data_for_input.txt"
    ```

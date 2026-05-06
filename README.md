# rad_nlp_anonymizer

## Overview
Anonymizer tool for radiological reports and other similar medical texts. Anonymizes sensitive information (names, emails, dates, and Finnish social security numbers).

Based on the anonymization tool implementation in: https://medium.com/@mithilesh007/a-simple-way-to-anonymize-texts-locally-safeguard-finnish-phi-with-this-tool-d8e9adf97e38

## Features
- Anonymizes names, email addresses, dates, and Finnish social security numbers.
- Supports input and output text files as well as SQLite databases.

## Requirements
- Python 3.9+
- Dependencies listed in `environment.yml`

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/tnissinen/custom-text-anonymization-tool.git
    cd custom-text-anonymization-tool
    ```

2. Create and activate the conda environment:
    ```sh
    conda env create -f environment.yml
    conda activate text_processor
    ```

3. Run the `nlp_pull_code.py` script to download and save the models:
    ```sh
    python nlp_pull_code.py
    ```

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
   
## Usage (SQLite db)

1. Prepare your SQLite database with the appropriate schema:

2. Configure database table names etc. in config.json:
   
3. Run the main.py script:
    ```sh
    python main.py
    ```


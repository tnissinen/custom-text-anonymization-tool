# Text Anonymization Tool

## Overview
This tool anonymizes sensitive information in text files, including personal names, email addresses, Finnish social security numbers (Hetu), and other identifiable information using NLP.

Medium article with examples: https://medium.com/@mithilesh007/a-simple-way-to-anonymize-texts-locally-safeguard-finnish-phi-with-this-tool-d8e9adf97e38

For LLM based approach follow the article on https://medium.com/@mithilesh007/️-enhancing-text-anonymization-with-ollama-a-smarter-alternative-to-traditional-nlp-05f66618aec2 

## Features
- Anonymizes personal names, email addresses, and Finnish social security numbers.
- Supports additional entity types such as organizations, locations, and dates.
- Flexible path configuration for input and output files.

## Requirements
- Python 3.9+
- Dependencies listed in `environment.yml`

## Installation
1. Clone the repository:
    ```sh
    git clone https://github.com/mithp/text-anonymization-tool.git
    cd text-anonymization-tool
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

## Usage
1. Define the base path for your files in the script:
    ```python
    base_path = "//your/base/path/"
    ```

2. Place your input text file in the appropriate directory:
    ```plaintext
    base_path + "input_output_text_files/your_input_file.txt"
    ```

3. Run the text anonymization script:
    ```sh
    python text_anonymization_tool.py
    ```

4. The redacted output will be saved in the specified output directory:
    ```plaintext
    base_path + "input_output_text_files/data_for_input.txt"
    ```

## Example (Gibberish text)
1. Create a sample input file `your_input_file.txt` with the following content:
    ```plaintext
    Potilas 1: Nimi: Mattii Meeikkäläineeen, Syntymäaika: 12.05.1234, Sähköposti: etu.sukunimi@example.com, Hetu: 123456-123A, Osoite: Tervekatu 1, Helsinki, Diagnoosi: Diabetes, Historia: Potilas on ollut diabeteksen hoidossa 10 vuotta. Verensokeritasot ovat olleet hyvin hallinnassa insuliinihoidolla. Verotiedot: Tulot: 50,000€, Veronumero: 123456789
    ```

2. Run the text anonymization script:
    ```sh
    python text_anonymization_tool.py
    ```

3. Check the output file `data_for_output.txt` for the redacted content.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.


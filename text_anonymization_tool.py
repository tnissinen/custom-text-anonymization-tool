import time
import re
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from unidecode import unidecode

base_path = "C:/Users/tomin/PycharmProjects/custom-text-anonymization-tool/"
IGNORE_WORD_LIST = ['vuoden', 'thoraxrontgen', 'thorax', 'thoraxin', 'thor', 'sope', 'vertailussa', 'arkisto', 'ster', 'lumen', 'pacs', 'pacsissa', 'issa', '.', ',', '!', '?', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '-', '_', '/', '\\']
SIMPLE_TAGS = True
IGNORE_WORD_LIST = ['date', 'name', 'vuoden', 'thoraxrontgen', 'thorax', 'thoraxin', 'thor', 'trochanter', 'sternumin', 'sternum', 'sope', 'vertailussa', 'arkisto', 'ster', 'lumen', 'pacs', 'pacsissa', 'issa', '.', ',', '!', '?', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '-', '_', '/', '\\']


class TextProcessor:
    def __init__(self):
        # Initialize NLP pipelines
        self.pipe_translate = None
        self.pipe_biomedical = None
        self.nlp = None
        self.simple_tags = True

        # Regular expression patterns for additional replacements
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ssn_pattern = re.compile(r'\b\d{2}\d{2}\d{2}[-+A]\d{3}[0-9A-FHJKLMNPRSTUVWXY]\b', re.I)
        self.difficult_names_to_replace = ['Juvakka', 'Hartikainen', 'Anu', 'Arponen', 'Amro', 'Masarwah', 'Tiihonen', 'Ranta', 'Hämäläinen']
        self.time_pattern = re.compile(r'\b(?:[01]?\d|2[0-3]):[0-5]\d\b')  # Matches HH:MM format
        self.date_patterns = [
            # 12.3.2022, 1.5.21, 12.3.2022 (dot-separated)
            r'\b(?:0?[1-9]|[12][0-9]|3[01])\.(?:0?[1-9]|1[0-2])\.?(?:\d{2,4})?\b',
            # 12.3 (dot-separated, no year)
            r'\b(?:0?[1-9]|[12][0-9]|3[01])\.(?:0?[1-9]|1[0-2])\b',
            # 2021-10-15 (ISO-style, year-month-day)
            r'\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])\b',
            # 211015 or 20211015 (compact numeric date)
            # Matches yymmdd or yyyymmdd — limited by plausible ranges
            r'\b(?:(?:\d{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])|(?:\d{4})(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01]))\b',
            # Matches ddmmyyyy or ddmmyy — limited by plausible ranges
            r'\b(?:(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])(?:\d{2})|(?:0[1-9]|[12][0-9]|3[01])(?:0[1-9]|1[0-2])(?:\d{4}))\b',
            # 15/10 or 15/10/2021, 5/1/21 (slash-separated)
            r'\b(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])(?:/\d{2,4})?\b',
            # 11/2021 or 03/21
            r'\b(?:0?[1-9]|1[0-2])(?:/\d{2,4})\b'
        ]

    def get_nlp(self):
        """ Initialize the NLP pipeline if not already done"""
        if self.nlp is None:
            self.nlp = pipeline("ner", model=base_path + "iguanodon-ai/bert-base-finnish-uncased-ner", aggregation_strategy='max')  # aggregation_strategy= simple, first, average or max
        return self.nlp

    def preprocess_text(self, text):
        """ Preprocess the text: strip whitespaces, normalize Unicode, and convert to lowercase"""
        text = text.strip()
        #text = unidecode(text)  # Normalize Unicode characters to ASCII, not in use for now
        #return text.lower()  # Convert to lowercase, not in use for now
        return text

    def replace_emails(self, text):
        """ Replaces email addresses in the text with a placeholder. """
        found_strings = []
        found_strings.extend(re.findall(self.email_pattern, text))
        return self.email_pattern.sub('*EMAIL*', text), found_strings

    def replace_finnish_ssn(self, text):
        """ Replaces Finnish SSNs in the text with a placeholder. """
        found_strings = []
        found_strings.extend(re.findall(self.ssn_pattern, text))
        return self.ssn_pattern.sub('*HETU*', text), found_strings

    def replace_difficult_names(self, text):
        """ Replaces specific difficult names in the text with placeholders. """

        found_names = []

        for name in self.difficult_names_to_replace:
            pattern = r'\b' + re.escape(name) + r'\b'
            found_names.extend(re.findall(pattern, text))

            if self.simple_tags:
                text = re.sub(pattern, '*NAME*', text, flags=re.IGNORECASE)
            else:
                text = re.sub(pattern, '*R-NAME*', text, flags=re.IGNORECASE)

        return text, found_names

    def replace_time_regex(self, text):
        """ Replaces time patterns in the text with a placeholder. """
        found_strings = []
        found_strings.extend(re.findall(self.time_pattern, text))
        return self.time_pattern.sub('*TIME*', text), found_strings

    def replace_dates_regex(self, text):
        """ Replaces date patterns in the text with a placeholder. """

        date_patterns = self.date_patterns
        found_dates = []
        for pat in date_patterns:
            found_dates.extend(re.findall(pat, text))

            if self.simple_tags:
                text = re.sub(pat, '*DATE*', text)
            else:
                text = re.sub(pat, '*R-DATE*', text)

        return text, found_dates

    def process_text(self, input_text):
        """ Process a single chunk of text and redact sensitive information. """

        detected_words = []
        redacted_words = []
        word_types = []

        # 1. Preprocess the input text
        processed_line = self.preprocess_text(input_text)

        # 2. Replace emails and Finnish SSNs
        redacted_line, found_emails = self.replace_emails(processed_line)
        redacted_line, found_ssns = self.replace_finnish_ssn(redacted_line)

        for found_email in found_emails:
            if found_email not in detected_words:
                detected_words.append(found_email)
                redacted_words.append('*R-EMAIL*')
                word_types.append('R-EMAIL')

        for found_ssn in found_ssns:
            if found_ssn not in detected_words:
                detected_words.append(found_ssn)
                redacted_words.append('*R-HETU*')
                word_types.append('R-HETU')

        # 3. Replace dates and times using regex
        redacted_line, found_dates = self.replace_dates_regex(redacted_line)
        redacted_line, found_times = self.replace_time_regex(redacted_line)

        for found_date in found_dates:
            if found_date not in detected_words:
                detected_words.append(found_date)
                redacted_words.append('*R-DATE*')
                word_types.append('R-DATE')

        for found_time in found_times:
            if found_time not in detected_words:
                detected_words.append(found_time)
                redacted_words.append('*R-TIME*')
                word_types.append('R-TIME')

        # 4. Use NLP model to identify and redact named entities
        nlp_results = self.get_nlp()(redacted_line)

        orig_redacted_line = redacted_line  # Keep the original line for reference

        for result in nlp_results:

            # Only consider specific entity types for redaction
            if result['entity_group'] in ['B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-DATE', 'I-DATE', 'DATE', 'PER', 'ORG', 'LOC']:

                # Skip short words that are not dates (they are likely not names)
                if result['entity_group'] not in ['B-DATE', 'I-DATE', 'DATE'] and len(result['word']) < 4:
                    continue

                # Skip words in the ignore list
                if result['word'] in IGNORE_WORD_LIST:
                    continue

                # get orig word based on start and end positions
                orig_word = orig_redacted_line[result['start']:result['end']]

                # Skip if the word is not found in the current redacted line (case insensitive) --> means it was already redacted by regex
                if redacted_line.lower().find(result['word']) == -1:

                    if orig_word.lower() == result['word'].lower():  # not because of case or äöå
                        continue

                # Create the redacted word based on the entity type
                redacted_word = f"*{result['entity_group']}*"
                redacted_words.append(redacted_word)

                # Escape special characters in the word for regex replacement
                pattern_for_replacement = r'\b' + re.escape(result['word']) + r'\b'

                if orig_word.lower() != result['word'].lower():
                    pattern_for_replacement = r'\b' + re.escape(orig_word) + r'\b'
                    print(f"!!!!!!Using orig word for replacement: {orig_word} instead of {result['word']}")

                if self.simple_tags:

                    # replace all date tags with a simple *DATE* tag
                    if result['entity_group'] in ['B-DATE', 'I-DATE', 'DATE']:
                        redacted_word = '*DATE*'
                    # replace all other tags with a simple *NAME* tag
                    else:
                        redacted_word = '*NAME*'

                # Replace the detected word in the line with the redacted word (case insensitive)
                redacted_line = re.sub(pattern_for_replacement, redacted_word, redacted_line, flags=re.IGNORECASE)

                detected_words.append(result['word'])
                word_types.append(result['entity_group'])

        # 5. Replace specific difficult names
        redacted_line, found_difficult_names = self.replace_difficult_names(redacted_line)

        for found_difficult_name in found_difficult_names:
            if found_difficult_name not in detected_words:
                detected_words.append(found_difficult_name)
                redacted_words.append('*R-NAME*')
                word_types.append('R-NAME')

        return redacted_line, detected_words, redacted_words, word_types

    def process_text_file(self, filename):
        """ Process a text file and redact sensitive information line by line. """

        redacted_lines = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                redacted_line_finer, _, _, _ = self.process_text(line)
                redacted_lines.append(redacted_line_finer)
                redacted_lines.append('\n')  # Append a blank line

        return list(filter(None, redacted_lines))

    def write_output(self, redacted_output, location_path):
        """ Write the redacted output to a file"""

        with open(location_path, 'w', encoding='utf-8') as f:
            for line in redacted_output:
                f.write(line)


# Main execution for testing, for database processing see main.py
if __name__ == '__main__':

    # Measure the execution time
    start_time = time.time()
    text_processor = TextProcessor()

    # Process the input text file and write the redacted output to a file
    redacted_output = text_processor.process_text_file(base_path + "input_output_text_files/your_input_file.txt")
    text_processor.write_output(redacted_output, base_path + "input_output_text_files/data_for_output.txt")

    print("--- %s seconds ---" % (time.time() - start_time))

import time
import os
import re
import json
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from unidecode import unidecode


class TextProcessor:
    def __init__(self, base_path=None, config_file=None):

        # Initialize NLP pipelines
        self.base_path = base_path if base_path is not None else os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config(config_file)
        self.pipe_translate = None
        self.pipe_biomedical = None
        self.nlp = None
        self.entity_groups = {'B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-DATE', 'I-DATE', 'DATE', 'PER', 'ORG', 'LOC'}

        # Set words to ignore from default and config
        self.ignore_words = {'date', 'name', 'vuoden', 'thoraxrontgen', 'thorax', 'thoraxin', 'thor', 'trochanter', 'sternumin', 'sternum', 'sope', 'vertailussa', 'arkisto', 'ster', 'lumen', 'pacs', 'pacsissa', 'issa', '.', ',', '!', '?', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '-', '_', '/', '\\'}
        if 'ignore_words' in self.config and isinstance(self.config['ignore_words'], list):
            self.ignore_words.update(self.config['ignore_words'])
            self.ignore_words = {word.lower() for word in self.ignore_words} # make sure words are lowercase

        # Regular expression patterns for additional replacements
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ssn_pattern = re.compile(r'\b\d{2}\d{2}\d{2}[-+A]\d{3}[0-9A-FHJKLMNPRSTUVWXY]\b', re.I)
        self.difficult_names_to_replace = {'Juvakka', 'Hartikainen', 'Anu', 'Arponen', 'Amro', 'Masarwah', 'Tiihonen', 'Ranta', 'Hämäläinen', "Harju", "Pitkänen", "Kettunen"}

        if 'names_to_anonymize' in self.config and isinstance(self.config['names_to_anonymize'], list):
            self.difficult_names_to_replace.update(self.config['names_to_anonymize'])
            self.difficult_names_to_replace = {word.lower() for word in self.difficult_names_to_replace}  # make sure words are lowercase

        self.time_pattern = re.compile(r'\b(?:[01]?\d|2[0-3]):[0-5]\d\b')  # Matches HH:MM format
        self.date_patterns = [
            # 12.3.2022, 1.5.21, 12.3.2022 (dot-separated) + negative lookahead to avoid matching measurements like 12.3 cm or 12.3mm
            r'\b(?:0?[1-9]|[12][0-9]|3[01])\.(?:0?[1-9]|1[0-2])\.?(?:\d{2,4})?(?!\s?(?:cm|mm))\b',
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
        """ Initialize the NLP pipeline if not already done and prefer GPU when available.
        Falls back to CPU if torch is not installed or CUDA is unavailable.
        """
        if self.nlp is None:
            model_path = self.base_path + "/iguanodon-ai/bert-base-finnish-uncased-ner"
            # Determine device safely without requiring torch at module import time
            try:
                import torch
                device = 0 if torch.cuda.is_available() else -1
            except Exception:
                device = -1

            self.nlp = pipeline(task="ner", model=model_path, aggregation_strategy='max', device=device)

        return self.nlp

    def load_config(self, config_path=None):
        """ Load configuration from a JSON file and set defaults for missing values """

        if config_path is None:
            config_path = self.base_path + "/config.json"

        defaults = {
            "printing": True,
            "simple_tags": True,
            "max_rows": 100000,
            "ignore_words": [],
            "redact_dates": True,
            "batch_size": 1000
        }
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Set defaults for missing values
        for key, value in defaults.items():
            config.setdefault(key, value)

        return config

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

            if self.config['simple_tags']:
                text = re.sub(pattern, '*NAME*', text, flags=re.IGNORECASE)
            else:
                text = re.sub(pattern, '*R-NAME*', text, flags=re.IGNORECASE)

        return text, found_names

    def replace_time_regex(self, text):
        """ Replaces time patterns in the text with a placeholder. Honor config['redact_dates'].
        """
        if not self.config.get('redact_dates', True):
            return text, []
        found_strings = []
        found_strings.extend(re.findall(self.time_pattern, text))
        return self.time_pattern.sub('*TIME*', text), found_strings

    def replace_dates_regex(self, text):
        """ Replaces date patterns in the text with a placeholder. Honor config['redact_dates']. """
        if not self.config.get('redact_dates', True):
            return text, []

        date_patterns = self.date_patterns
        found_dates = []
        for pat in date_patterns:
            found_dates.extend(re.findall(pat, text))

            if self.config['simple_tags']:
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
        preprocessed_text = self.preprocess_text(input_text)

        # 2. Replace emails and Finnish SSNs
        redacted_line, found_emails = self.replace_emails(preprocessed_text)
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

            # Skip date entities entirely if config disables date redaction
            if result.get('entity_group') in ['B-DATE', 'I-DATE', 'DATE'] and not self.config.get('redact_dates', True):
                continue

            # Only consider specific entity types for redaction
            if result['entity_group'] in self.entity_groups:

                # Skip short words that are not dates (they are likely not names)
                if result['entity_group'] not in ['B-DATE', 'I-DATE', 'DATE'] and len(result['word']) < 4:
                    continue

                # Skip words in the ignore list
                if result['word'] in self.ignore_words:
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
                    #print(f"Using orig word {orig_word} instead of {result['word']} for replacement")

                if self.config['simple_tags']:

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

    def process_batch(self, input_texts):
        """Process a batch of texts using regex preprocessing and a single batched NLP pipeline call.
        Returns a list of tuples: (redacted_line, detected_words, redacted_words, word_types) for each input.
        TODO: warning: vibe coded! refactor to avoid code duplication with process_text
        """
        # 1. Preprocess and run regex replacements for the whole batch
        pre_redacted = []
        pre_detected = []
        for input_text in input_texts:
            preprocessed_text = self.preprocess_text(input_text)
            redacted_line, found_emails = self.replace_emails(preprocessed_text)
            redacted_line, found_ssns = self.replace_finnish_ssn(redacted_line)
            redacted_line, found_dates = self.replace_dates_regex(redacted_line)
            redacted_line, found_times = self.replace_time_regex(redacted_line)

            pre_redacted.append(redacted_line)
            pre_detected.append({
                'emails': found_emails,
                'ssns': found_ssns,
                'dates': found_dates,
                'times': found_times
            })

        # 2. Run batched NER via the transformers pipeline to maximize GPU throughput
        nlp = self.get_nlp()
        # The pipeline accepts a list of strings and returns a list of lists of entity dicts
        nlp_results = nlp(pre_redacted)

        # 3. Apply NER results and postprocessing per item
        batch_outputs = []
        for idx, redacted_line in enumerate(pre_redacted):
            detected_words = []
            redacted_words = []
            word_types = []

            # include regex-detected items first
            for found_email in pre_detected[idx]['emails']:
                if found_email not in detected_words:
                    detected_words.append(found_email)
                    redacted_words.append('*R-EMAIL*')
                    word_types.append('R-EMAIL')

            for found_ssn in pre_detected[idx]['ssns']:
                if found_ssn not in detected_words:
                    detected_words.append(found_ssn)
                    redacted_words.append('*R-HETU*')
                    word_types.append('R-HETU')

            for found_date in pre_detected[idx]['dates']:
                if found_date not in detected_words:
                    detected_words.append(found_date)
                    redacted_words.append('*R-DATE*')
                    word_types.append('R-DATE')

            for found_time in pre_detected[idx]['times']:
                if found_time not in detected_words:
                    detected_words.append(found_time)
                    redacted_words.append('*R-TIME*')
                    word_types.append('R-TIME')

            orig_redacted_line = redacted_line

            # nlp_results may be a list-of-lists (one list per input)
            item_results = nlp_results[idx] if isinstance(nlp_results, list) and len(nlp_results) > idx else []

            for result in item_results:
                # Skip date entities entirely if config disables date redaction
                if result.get('entity_group') in ['B-DATE', 'I-DATE', 'DATE'] and not self.config.get('redact_dates', True):
                    continue

                # Only consider specific entity types for redaction
                if result.get('entity_group') in self.entity_groups:
                    # Skip short words that are not dates
                    if result['entity_group'] not in ['B-DATE', 'I-DATE', 'DATE'] and len(result.get('word', '')) < 4:
                        continue

                    # Skip words in the ignore list
                    if result.get('word') in self.ignore_words:
                        continue

                    # get orig word based on start and end positions
                    start = result.get('start')
                    end = result.get('end')
                    if start is None or end is None:
                        continue
                    orig_word = orig_redacted_line[start:end]

                    # Skip if the word is not found in the current redacted line (case insensitive)
                    if redacted_line.lower().find(result.get('word', '').lower()) == -1:
                        if orig_word.lower() == result.get('word', '').lower():
                            continue

                    # Create the redacted word based on the entity type
                    redacted_word = f"*{result['entity_group']}*"

                    # Escape special characters in the word for regex replacement
                    pattern_for_replacement = r'\b' + re.escape(result.get('word', '')) + r'\b'

                    if orig_word.lower() != result.get('word', '').lower():
                        pattern_for_replacement = r'\b' + re.escape(orig_word) + r'\b'

                    if self.config.get('simple_tags', True):
                        # replace all date tags with a simple *DATE* tag
                        if result['entity_group'] in ['B-DATE', 'I-DATE', 'DATE']:
                            redacted_word = '*DATE*'
                        else:
                            redacted_word = '*NAME*'

                    # Replace the detected word in the line with the redacted word (case insensitive)
                    redacted_line = re.sub(pattern_for_replacement, redacted_word, redacted_line, flags=re.IGNORECASE)

                    detected_words.append(result.get('word'))
                    word_types.append(result.get('entity_group'))
                    redacted_words.append(redacted_word)

            # 4. Replace specific difficult names
            redacted_line, found_difficult_names = self.replace_difficult_names(redacted_line)

            for found_difficult_name in found_difficult_names:
                if found_difficult_name not in detected_words:
                    detected_words.append(found_difficult_name)
                    redacted_words.append('*R-NAME*')
                    word_types.append('R-NAME')

            batch_outputs.append((redacted_line, detected_words, redacted_words, word_types))

        return batch_outputs

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

    app_path = os.path.dirname(os.path.abspath(__file__))

    # Measure the execution time
    start_time = time.time()
    text_processor = TextProcessor(base_path=app_path)

    # Process the input text file and write the redacted output to a file
    redacted_output = text_processor.process_text_file(app_path + "/input_output_text_files/your_input_file.txt")
    text_processor.write_output(redacted_output, app_path + "/input_output_text_files/data_for_output.txt")

    print("--- %s seconds ---" % (time.time() - start_time))

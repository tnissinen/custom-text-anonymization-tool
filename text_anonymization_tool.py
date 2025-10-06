import time
import re
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from unidecode import unidecode

# Define the base path variable
base_path = "C:/Users/tomni/PycharmProjects/custom-text-anonymization-tool/"

class TextProcessor:
    def __init__(self):
        self.pipe_translate = None
        self.pipe_biomedical = None
        self.nlp = None
        # Regular expression patterns for email and Finnish SSN format
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ssn_pattern = re.compile(r'\b\d{2}\d{2}\d{2}[-+A]\d{3}[0-9A-FHJKLMNPRSTUVWXY]\b', re.I)

    def get_nlp(self):
        # Initialize the NLP pipeline if not already done
        if self.nlp is None:
            self.nlp = pipeline("ner", model=base_path + "iguanodon-ai/bert-base-finnish-uncased-ner")
        return self.nlp

    def preprocess_text(self, text):
        # Preprocess the text: strip whitespaces, normalize Unicode, and convert to lowercase
        text = text.strip()
        #text = unidecode(text)
        #return text.lower()
        return text

    def replace_emails(self, text):
        # Replace email addresses with a placeholder
        return self.email_pattern.sub('--**email**--', text) #Change as per your needs

    def replace_finnish_ssn(self, text):
        # Replace Finnish SSNs with a placeholder
        return self.ssn_pattern.sub('--**hetu**--', text) #Change as per your needs

    def redact_names(self, line):
        # Redact names and other entities using the NLP pipeline
        detected_words = []
        redacted_words = []
        word_types = []
        processed_line = self.preprocess_text(line)
        redacted_line = self.replace_emails(processed_line)
        redacted_line = self.replace_finnish_ssn(redacted_line)

        for result in self.get_nlp()(redacted_line):
            if result['entity'] in ['B-PER', 'I-PER', 'B-ORG', 'I-ORG', 'B-LOC', 'I-LOC', 'B-DATE', 'I-DATE']: #list can be customized.

                if result['entity'] not in ['B-DATE', 'I-DATE'] and len(result['word']) < 4:  # Skip short words except in dates
                    continue

                if result['word'] in ['.', ',', '!', '?', ':', ';', '(', ')', '[', ']', '{', '}', '"', "'", '-', '_', '/', '\\']:
                    continue

                if redacted_line.find(result['word']) == -1:
                    continue

                redacted_word = f"*{result['entity']}*"
                pattern = re.escape(result['word'])
                redacted_line = re.sub(pattern, redacted_word, redacted_line, flags=re.IGNORECASE)
                detected_words.append(result['word'])
                redacted_words.append(redacted_word)
                word_types.append(result['entity'])
        return redacted_line, detected_words, redacted_words, word_types

    def process_text_file(self, filename):
        # Process the text file and redact sensitive information
        redacted_lines = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                redacted_line_finer, _, _, _ = self.redact_names(line)
                redacted_lines.append(redacted_line_finer)
                redacted_lines.append('\n')  # Append a blank line
        return list(filter(None, redacted_lines))

    def write_output(self, redacted_output, location_path):
        # Write the redacted output to a file
        with open(location_path, 'w', encoding='utf-8') as f:
            for line in redacted_output:
                f.write(line)

    def clean_write(self, redacted_output, location_path):
        # Placeholder method for clean writing (not implemented)
        return 0


if __name__ == '__main__':
    # Measure the execution time
    start_time = time.time()
    text_processor = TextProcessor()
    # Process the input text file and write the redacted output to a file
    redacted_output = text_processor.process_text_file(base_path + "input_output_text_files/your_input_file.txt")
    text_processor.write_output(redacted_output, base_path + "input_output_text_files/data_for_output.txt")
    print("--- %s seconds ---" % (time.time() - start_time))

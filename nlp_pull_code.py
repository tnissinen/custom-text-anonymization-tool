from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

# Define the folder path for saving models and tokenizers
folder_on_save = 'C:/Users/tomin/PycharmProjects/custom-text-anonymization-tool/'

# Define full paths for each model and tokenizer
full_path_01 = folder_on_save + 'iguanodon-ai/bert-base-finnish-uncased-ner'

# These 2 are optional but could be useful for english names and etc.
full_path_02 = folder_on_save + 'facebook/mbart-large-50-many-to-many-mmt'
full_path_03 = folder_on_save + 'd4data/biomedical-ner-all'


def save_model_and_tokenizer(model_name, full_path):
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.save_pretrained(full_path)
    model.save_pretrained(full_path)


def save_translation_model_and_tokenizer(model_name, full_path):
    model = MBartForConditionalGeneration.from_pretrained(model_name)
    tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
    tokenizer.save_pretrained(full_path)
    model.save_pretrained(full_path)

# Save models and tokenizers
save_model_and_tokenizer("iguanodon-ai/bert-base-finnish-uncased-ner", full_path_01)
#save_translation_model_and_tokenizer("facebook/mbart-large-50-many-to-many-mmt", full_path_02)
#save_model_and_tokenizer("d4data/biomedical-ner-all", full_path_03)

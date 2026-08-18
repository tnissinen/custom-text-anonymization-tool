import os
from transformers import AutoModelForTokenClassification, AutoTokenizer

# Define the folder path for saving models and tokenizers
folder_on_save = os.path.dirname(os.path.realpath(__file__))

# Define full paths for each model and tokenizer
full_path_01 = folder_on_save + '/iguanodon-ai/bert-base-finnish-uncased-ner'

def save_model_and_tokenizer(model_name, full_path):
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.save_pretrained(full_path)
    model.save_pretrained(full_path)

# Save models and tokenizers
save_model_and_tokenizer("iguanodon-ai/bert-base-finnish-uncased-ner", full_path_01)
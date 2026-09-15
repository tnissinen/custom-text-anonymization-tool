import sys
import time
import utils
from text_anonymization_tool import TextProcessor
from excel_processing import anonymize_excel
from db_processing import anonymize_db


def anonymize_records(config_path):
    """Run anonymization for either Excel or SQLite input."""
    text_processor = TextProcessor(config_file=config_path)
    config = text_processor.config

    if config.get('use_excel', False):
        return anonymize_excel(text_processor, config)

    return anonymize_db(text_processor, config)


if __name__ == '__main__':

    # check and report GPU availability
    utils.check_torch_gpu()

    # check model and download if needed (first run)
    model_repo = "iguanodon-ai/bert-base-finnish-uncased-ner"
    utils.check_model_and_tokenizer(model_repo)

    # measure total processing time
    start_time = time.perf_counter()

    # read first command-line argument as config path (optional)
    config_from_parameter = sys.argv[1] if len(sys.argv) > 1 else None

    # run anonymization
    anonymize_records(config_from_parameter)

    total_time = time.perf_counter() - start_time
    print("Total processing time: {:.1f}s".format(total_time))


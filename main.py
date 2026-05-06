import sqlite3
import time
from text_anonymization_tool import TextProcessor


def run_anonymize_for_db(input_column=None, table_name=None):
    """Anonymize text data in a specified column of a database table."""

    global text_processor

    if input_column is None or input_column == "":
        # use default columns
        input_column = text_processor.config['input_column']
        output_column = text_processor.config['output_column']
        score_column = text_processor.config['score_column']
        info_column = text_processor.config['info_column']
    else:
        # create output, score, and warning column names based on input column
        output_column = f"{input_column}_anon"
        score_column = f"{input_column}_anon_score"
        info_column = f"{input_column}_anon_info"

    if table_name is None or table_name == "":
        # use default table name
        table_name = text_processor.config['table_name']

    db_path = text_processor.config['db_path']
    id_column = text_processor.config['id_column']
    min_id = text_processor.config.get('min_id', 0)
    max_id = text_processor.config.get('max_id', 1000000)
    printing = text_processor.config.get('printing', True)

    print(f"Running anonymize to db: {db_path}")
    print(f"Table: {table_name}, input column: {input_column}, output column: {output_column}, score column: {score_column}")

    # connect to the database and create cursors for selecting and updating
    conn = sqlite3.connect(db_path)
    select_cursor = conn.cursor()
    update_cursor = conn.cursor()

    # create the query to select rows with non-null and non-empty input column values
    query_text = f"SELECT {id_column}, {input_column} FROM {table_name} WHERE {input_column} is not null and {input_column} != '-'"
    query_text += f" and {id_column} >= {min_id} and {id_column} <= {max_id}"

    # count the number of rows to be processed
    query_row_count = "SELECT COUNT(*) FROM ({})".format(query_text)
    select_cursor.execute(query_row_count)
    row_count = select_cursor.fetchone()[0]
    print("Processing rows: ", row_count)

    # if row count is over 1000 rows, disable global printing
    if row_count >= 100:
        printing = False
        print("Disabling printing for over 100 rows")

    # execute the actual rows query
    select_cursor.execute(query_text)

    updated_rows = 0
    processed_rows = 0

    # iterate over the db rows
    for row in select_cursor:

        row_id, report_text = row

        if printing:
            print(f"Processing row ID: {row_id}, report text: {report_text[:50]}...")

        # process the text to redact names and other sensitive information
        redacted_text, detected_words, redacted_words, word_types = text_processor.process_text(report_text)

        processed_rows += 1

        # if any words were detected, update the database
        if len(detected_words) > 0:

            # turn unique detected_words and word_types into comma-separated strings
            warning_detected_types = ', '.join(set(word_types))
            warning_detected_words = ', '.join(set(detected_words))

            # combined warning message
            warning_message = f"{warning_detected_types}: {warning_detected_words}"

            if printing:
                print(f"Detected words: {detected_words}")
                print(f"Redacted words: {redacted_words}")
                print(f"Word types: {word_types}")

            # Update the database with the redacted text
            update_query = f"UPDATE {table_name} SET {output_column} = ?, {score_column} = ?, {info_column} = ? WHERE {id_column} = ?"
            update_cursor.execute(update_query, (redacted_text, len(detected_words), warning_message, row_id))
            updated_rows += 1
        else:
            if printing:
                print(f"No sensitive information detected in row ID: {row_id}")

        # report progress every 1000 rows
        if processed_rows % 1000 == 0:
            print(f"Reports processed: {processed_rows}, reports updated: {updated_rows}")

    print("\n---------All rows processed---------------")
    print(f"Total reports processed: {processed_rows}, total reports updated: {updated_rows}")
    print("\ncommitting changes to the database...")

    # commit the changes and close the cursors
    conn.commit()
    select_cursor.close()
    update_cursor.close()

    print("\nDONE\n")


if __name__ == '__main__':

    start_time = time.perf_counter()

    # create an instance of the TextProcessor (contains the actual processing logic), and load the config
    text_processor = TextProcessor()
    text_processor.load_config()


    run_anonymize_for_db()

    #run_anonymize_for_db("report1")
    #run_anonymize_for_db("request1")
    #run_anonymize_for_db("report2")
    #run_anonymize_for_db("request2")

    #run_anonymize_for_db(input_column="Lausuntoteksti", table_name="Lausunnot_Xray_CT")

    #run_anonymize_for_db(input_column="Lausuntoteksti", table_name="Lausunnot_10000")
    #run_anonymize_for_db(input_column="report_en", table_name="Lausunnot_10000")
    #run_anonymize_for_db(input_column="report_fin", table_name="Lausunnot_10000")

    total_time = time.perf_counter() - start_time
    print("Total processing time: {:.1f}s".format(total_time))
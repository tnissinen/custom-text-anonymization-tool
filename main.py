import sqlite3
from text_anonymization_tool import TextProcessor

DB_PATH = "c:/temp/xray/xray.db"  # Replace with your actual database path
TABLE_NAME = "xray_ordered"  # Replace with your actual table name
ID_COLUMN = "rownum"  # Replace with your actual ID column name
INPUT_COLUMN = "field7"  # Replace with your actual column name
OUTPUT_COLUMN = "anonymized_text"  # Replace with your actual result column name
SCORE_COLUMN = "anonymized_score"  # Replace with your actual score column name
WARNING_COLUMN = "anonymization_warnings"  # Replace with your actual warning column name
printing = True  # Global variable to control printing


def run_anonymize_for_db(input_column=None, table_name=None):
    global printing

    if input_column is None or input_column == "":
        input_column = INPUT_COLUMN
        output_column = OUTPUT_COLUMN
        score_column = SCORE_COLUMN
        warning_column = WARNING_COLUMN
    else:
        output_column = f"{input_column}_anon"
        score_column = f"{input_column}_anon_score"
        warning_column = f"{input_column}_anon_info"

    if table_name is None or table_name == "":
        table_name = TABLE_NAME

    print(f"Running anonymize to db: {DB_PATH}")

    print(f"Table: {table_name}, input column: {input_column}, output column: {output_column}, score column: {score_column}")

    conn = sqlite3.connect(DB_PATH)
    select_cursor = conn.cursor()
    update_cursor = conn.cursor()

    query_text = f"SELECT {ID_COLUMN}, {input_column} FROM {table_name} WHERE {input_column} is not null and {input_column} != '-'"
    query_text += f" and {ID_COLUMN} >= 0 and {ID_COLUMN} <= 1000000"

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

    text_processor = TextProcessor()
    # iterate over the db rows
    for row in select_cursor:

        row_id, report_text = row

        if printing:
            print(f"Processing row ID: {row_id}, report text: {report_text[:50]}...")

        redacted_text, detected_words, redacted_words, word_types = text_processor.redact_names(report_text)

        processed_rows += 1

        if len(detected_words) > 0:

            # turn unique detected_words and word_types into comma-separated strings
            warning_detected_types = ', '.join(set(word_types))
            warning_detected_words = ', '.join(set(detected_words))

            # combied warning message
            warning_message = f"{warning_detected_types}: {warning_detected_words}"

            if printing:
                print(f"Detected words: {detected_words}")
                print(f"Redacted words: {redacted_words}")
                print(f"Word types: {word_types}")

            # Update the database with the redacted text
            update_query = f"UPDATE {table_name} SET {output_column} = ?, {score_column} = ?, {warning_column} = ? WHERE {ID_COLUMN} = ?"
            update_cursor.execute(update_query, (redacted_text, len(detected_words), warning_message, row_id))
            updated_rows += 1
        else:
            if printing:
                print(f"No sensitive information detected in row ID: {row_id}")

        if processed_rows % 1000 == 0:
            print(f"Reports processed: {processed_rows}, labels updated: {updated_rows}")

    print("\n---------All rows processed---------------")
    print(f"Total reports processed: {processed_rows}, total labels updated: {updated_rows}")
    print("\ncommitting changes to the database...")

    # commit the changes and close the cursors
    conn.commit()
    select_cursor.close()
    update_cursor.close()

    print("\nDONE\n")


if __name__ == '__main__':
    run_anonymize_for_db()

    #run_anonymize_for_db("report1")
    #run_anonymize_for_db("request1")
    #run_anonymize_for_db("report2")
    #run_anonymize_for_db("request2")

    #run_anonymize_for_db(input_column="Lausuntoteksti", table_name="Lausunnot_Xray_CT")

    #run_anonymize_for_db(input_column="Lausuntoteksti", table_name="Lausunnot_10000")
    #run_anonymize_for_db(input_column="report_en", table_name="Lausunnot_10000")
    #run_anonymize_for_db(input_column="report_fin", table_name="Lausunnot_10000")

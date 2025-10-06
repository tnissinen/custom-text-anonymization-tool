import sqlite3
from text_anonymization_tool import TextProcessor

DB_PATH = "c:/temp/xray/xray.db"  # Replace with your actual database path
TABLE_NAME = "xray_ordered"  # Replace with your actual table name
ID_COLUMN = "rownum"  # Replace with your actual ID column name
INPUT_COLUMN = "field7"  # Replace with your actual column name
OUTPUT_COLUMN = "anonymized_text"  # Replace with your actual result column name
SCORE_COLUMN = "anonymized_score"  # Replace with your actual score column name

printing = True  # Global variable to control printing


def run_anonymize_for_db():
    global printing

    print(f"Running anonymize to db: {DB_PATH}")

    print(f"Table: {TABLE_NAME}, input column: {INPUT_COLUMN}, output column: {OUTPUT_COLUMN}, score column: {SCORE_COLUMN}")

    conn = sqlite3.connect(DB_PATH)
    select_cursor = conn.cursor()
    update_cursor = conn.cursor()

    query_text = f"SELECT {ID_COLUMN}, {INPUT_COLUMN} FROM {TABLE_NAME} WHERE {INPUT_COLUMN} is not null and {INPUT_COLUMN} != '-'"
    query_text += f" and {ID_COLUMN} >= 3001 and {ID_COLUMN} <= 3101"

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
            if printing:
                print(f"Detected words: {detected_words}")
                print(f"Redacted words: {redacted_words}")
                print(f"Word types: {word_types}")

            # Update the database with the redacted text
            update_query = f"UPDATE {TABLE_NAME} SET {OUTPUT_COLUMN} = ?, {SCORE_COLUMN} = ? WHERE {ID_COLUMN} = ?"
            update_cursor.execute(update_query, (redacted_text, len(detected_words), row_id))
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
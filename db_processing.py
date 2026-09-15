import sqlite3


def anonymize_db(text_processor, config=None):
    """Anonymize a text column in a SQLite database table."""

    config = text_processor.config if config is None else config

    # Extract configuration parameters
    input_column = config['input_column']
    output_column = config['output_column']
    score_column = config['score_column']
    info_column = config['info_column']
    id_column = config['id_column']
    min_id = config.get('min_id', 0)
    max_id = config.get('max_id', 1000000)
    printing = config.get('printing', True)
    table_name = config['table_name']
    db_path = config['db_path']

    print(f"Running anonymize to db: {db_path}")
    print(f"Table: {table_name}, input column: {input_column}, output column: {output_column}, score column: {score_column}")

    # Connect to the SQLite database and create an index on the id column for faster lookups
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE INDEX IF NOT EXISTS id_column_index ON {}({})".format(table_name, id_column))

    select_cursor = conn.cursor()
    update_cursor = conn.cursor()

    # Construct the SQL query to select rows based on the input column and id range
    query_text = f"SELECT {id_column}, {input_column} FROM {table_name} WHERE {input_column} is not null and {input_column} != '-'"
    query_text += f" and {id_column} >= {min_id} and {id_column} <= {max_id}"

    query_row_count = "SELECT COUNT(*) FROM ({})".format(query_text)
    select_cursor.execute(query_row_count)
    row_count = select_cursor.fetchone()[0]
    print("Processing rows: ", row_count)

    # Disable printing if the number of rows exceeds 100 to avoid excessive output
    if row_count >= 100:
        printing = False
        print("Disabling printing for over 100 rows")

    updated_rows = 0
    processed_rows = 0
    batch_size = int(config.get('batch_size', 1000))
    offset = 0

    # Process the rows in batches to avoid loading all data into memory at once
    while True:

        # Use LIMIT and OFFSET to fetch a batch of rows from the database
        paged_query = query_text + " LIMIT ? OFFSET ?"
        select_cursor.execute(paged_query, (batch_size, offset))
        rows = select_cursor.fetchall()
        if not rows:
            break

        # Extract the row IDs and report texts from the fetched rows
        row_ids = [r[0] for r in rows]
        report_texts = [r[1] for r in rows]

        # Process the batch of report texts using the text processor
        batch_results = text_processor.process_batch(report_texts)

        # Iterate over the results of the batch processing and update the database accordingly
        for i, (redacted_text, detected_words, redacted_words, word_types) in enumerate(batch_results):
            processed_rows += 1
            row_id = row_ids[i]

            if printing:
                print(f"\nProcessing row ID: {row_id}, report text: {str(report_texts[i])[:200]}...")

            # If sensitive information is detected, prepare the score and warning message for database update
            if len(detected_words) > 0:
                score = len(detected_words)
                warning_detected_types = ', '.join(set(word_types))
                warning_detected_words = ', '.join(set(detected_words))
                warning_message = f"{warning_detected_types}: {warning_detected_words}"

                if printing:
                    print(f"Detected words: {detected_words}")
                    print(f"Redacted words: {redacted_words}")
                    print(f"Word types: {word_types}")

                updated_rows += 1
            else:
                if printing:
                    print(f"No sensitive information detected in row ID: {row_id}")
                redacted_text = report_texts[i]
                warning_message = None
                score = None

            # Update the database with the redacted text, score, and warning message for the current row
            update_query = f"UPDATE {table_name} SET {output_column} = ?, {score_column} = ?, {info_column} = ? WHERE {id_column} = ?"
            update_cursor.execute(update_query, (redacted_text, score, warning_message, row_id))

        conn.commit()

        if printing:
            print("")

        print(f"Reports processed: {processed_rows}, reports updated: {updated_rows}")
        offset += len(rows)

    print("\n---------All rows processed---------------")
    print(f"Total reports processed: {processed_rows}, total reports updated: {updated_rows}")
    print("\ncommitting final changes to the database (if any)...")

    # Commit any remaining changes to the database and close the cursors
    conn.commit()
    select_cursor.close()
    update_cursor.close()

    print("\nDONE\n")
    return conn

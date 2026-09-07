import sqlite3
import time
import sys
import utils
from text_anonymization_tool import TextProcessor



def anonymize_records(input_column=None, table_name=None):
    """Anonymize text data in a specified column of a database table or Excel file based on config."""

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

    # common config values
    id_column = text_processor.config['id_column']
    min_id = text_processor.config.get('min_id', 0)
    max_id = text_processor.config.get('max_id', 1000000)
    printing = text_processor.config.get('printing', True)
    use_excel = text_processor.config.get('use_excel', False)

    if use_excel:
        # Excel-based processing using openpyxl
        excel_path = text_processor.config['excel_path']
        print(f"Running anonymize to Excel: {excel_path}")
        print(f"Input column: {input_column}, output column: {output_column}, score column: {score_column}")

        try:
            import openpyxl
        except Exception:
            print("openpyxl is required for Excel processing. Install it with: pip install openpyxl")
            raise

        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active

        # Read header row (assumes headers are in the first row)
        header_cells = list(ws[1])
        headers = [str(c.value) if c.value is not None else '' for c in header_cells]

        if input_column not in headers:
            raise ValueError(f"Input column '{input_column}' not found in Excel headers: {headers}")

        # Helper to ensure an output column exists; returns 1-based column index
        def ensure_column(col_name):
            if col_name in headers:
                return headers.index(col_name) + 1
            # append new header cell at the end
            new_idx = len(headers) + 1
            ws.cell(row=1, column=new_idx, value=col_name)
            headers.append(col_name)
            return new_idx

        input_idx = headers.index(input_column) + 1
        id_idx = headers.index(id_column) + 1 if id_column in headers else None
        output_idx = ensure_column(output_column)
        score_idx = ensure_column(score_column)
        info_idx = ensure_column(info_column)

        # Build list of row indices to process (skip header row)
        rows_to_process = []
        for r in range(2, ws.max_row + 1):
            cell_val = ws.cell(row=r, column=input_idx).value
            if cell_val is None:
                continue
            if str(cell_val) == '-':
                continue
            if id_idx is not None:
                id_val = ws.cell(row=r, column=id_idx).value
                try:
                    if id_val is None:
                        continue
                    if not (min_id <= float(id_val) <= max_id):
                        continue
                except Exception:
                    # unable to interpret id value, skip row
                    continue
            rows_to_process.append(r)

        row_count = len(rows_to_process)
        print("Processing rows: ", row_count)

        if row_count >= 100:
            printing = False
            print("Disabling printing for over 100 rows")

        updated_rows = 0
        processed_rows = 0

        for r in rows_to_process:
            row_id = ws.cell(row=r, column=id_idx).value if id_idx is not None else r - 1
            report_text = ws.cell(row=r, column=input_idx).value

            if printing:
                display_text = str(report_text)[:50] if report_text is not None else ''
                print(f"Processing row ID: {row_id}, report text: {display_text}...")

            redacted_text, detected_words, redacted_words, word_types = text_processor.process_text(report_text)
            processed_rows += 1

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
                redacted_text = report_text
                warning_message = None
                score = None

            # write back to worksheet
            ws.cell(row=r, column=output_idx, value=redacted_text)
            ws.cell(row=r, column=score_idx, value=score)
            ws.cell(row=r, column=info_idx, value=warning_message)

            if processed_rows % 1000 == 0 and processed_rows > 0:
                print(f"Reports processed: {processed_rows}, reports updated: {updated_rows}")

        print("\n---------All rows processed---------------")
        print(f"Total reports processed: {processed_rows}, total reports updated: {updated_rows}")
        print(f"\nWriting changes to Excel: {excel_path}...")

        wb.save(excel_path)

        print("\nDONE\n")

    else:
        # SQLite database processing (existing behavior)
        table_name = table_name if (table_name is not None and table_name != "") else text_processor.config['table_name']
        db_path = text_processor.config['db_path']

        print(f"Running anonymize to db: {db_path}")
        print(f"Table: {table_name}, input column: {input_column}, output column: {output_column}, score column: {score_column}")

        # connect to the database and create cursors for selecting and updating
        conn = sqlite3.connect(db_path)

        # optimization: create index on id column if not exists for faster updates, especially if processing only a subset of the data based on id range
        conn.execute("CREATE INDEX IF NOT EXISTS id_column_index ON {}({})".format(table_name, id_column))

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

        # iterate over the db rows in batches using LIMIT/OFFSET and commit after each batch to reduce transaction size
        updated_rows = 0
        processed_rows = 0
        batch_size = int(text_processor.config.get('batch_size', 1000))
        offset = 0

        while True:
            # Fetch only batch_size rows using LIMIT/OFFSET
            paged_query = query_text + " LIMIT ? OFFSET ?"
            select_cursor.execute(paged_query, (batch_size, offset))
            rows = select_cursor.fetchall()
            if not rows:
                break

            # Prepare texts and IDs for batched processing
            row_ids = [r[0] for r in rows]
            report_texts = [r[1] for r in rows]

            # process the batch using the TextProcessor batched pipeline
            batch_results = text_processor.process_batch(report_texts)

            for i, (redacted_text, detected_words, redacted_words, word_types) in enumerate(batch_results):
                processed_rows += 1
                row_id = row_ids[i]

                if printing:
                    print(f"\nProcessing row ID: {row_id}, report text: {str(report_texts[i])[:50]}...")

                # if any words were detected, update the database
                if len(detected_words) > 0:
                    score = len(detected_words)  # number of detected words

                    # turn unique detected_words and word_types into comma-separated strings
                    warning_detected_types = ', '.join(set(word_types))
                    warning_detected_words = ', '.join(set(detected_words))

                    # combined warning message
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

                # Update the database with the redacted text
                update_query = f"UPDATE {table_name} SET {output_column} = ?, {score_column} = ?, {info_column} = ? WHERE {id_column} = ?"
                update_cursor.execute(update_query, (redacted_text, score, warning_message, row_id))

            # commit after each batch
            conn.commit()

            if printing:
                print("")

            print(f"Reports processed: {processed_rows}, reports updated: {updated_rows}")

            # Move to next page
            offset += len(rows)

        print("\n---------All rows processed---------------")
        print(f"Total reports processed: {processed_rows}, total reports updated: {updated_rows}")
        print("\ncommitting final changes to the database (if any)...")

        # final commit to ensure all changes persisted
        conn.commit()
        select_cursor.close()
        update_cursor.close()

        print("\nDONE\n")


if __name__ == '__main__':

    utils.check_torch_gpu()

    start_time = time.perf_counter()

    # read first command-line argument as config path (optional)
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    # create an instance of the TextProcessor with optional config_path
    text_processor = TextProcessor(config_file=config_path)

    anonymize_records()

    #anonymize_records("report1")
    #anonymize_records("report2")

    #anonymize_records(input_column="my_report_column", table_name="my_table")

    total_time = time.perf_counter() - start_time
    print("Total processing time: {:.1f}s".format(total_time))
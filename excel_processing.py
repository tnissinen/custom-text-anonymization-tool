def anonymize_excel(text_processor, config=None):
    """Anonymize a text column in an Excel workbook."""

    config = text_processor.config if config is None else config

    input_column = config['input_column']
    output_column = config['output_column']
    score_column = config['score_column']
    info_column = config['info_column']
    id_column = config['id_column']
    min_id = config.get('min_id', 0)
    max_id = config.get('max_id', 1000000)
    printing = config.get('printing', True)
    excel_path = config['excel_path']
    print(f"Running anonymize to Excel: {excel_path}")
    print(f"Input column: {input_column}, output column: {output_column}, score column: {score_column}")

    # Check if openpyxl is installed, and if not, raise an error with instructions to install it
    try:
        import openpyxl
    except Exception:
        print("openpyxl is required for Excel processing. Install it with: pip install openpyxl")
        raise

    # Load the Excel workbook and get the active worksheet
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    # Get the header row and create a list of headers, ensuring that None values are replaced with empty strings
    header_cells = list(ws[1])
    headers = [str(c.value) if c.value is not None else '' for c in header_cells]

    if input_column not in headers:
        raise ValueError(f"Input column '{input_column}' not found in Excel headers: {headers}")

    if id_column not in headers:
        raise ValueError(f"Id column '{id_column}' not found in Excel headers: {headers}")

    def ensure_column(col_name):
        """ Ensure that a column exists in the worksheet. If it doesn't, add it to the end of the header row."""

        if col_name in headers:
            return headers.index(col_name) + 1
        new_idx = len(headers) + 1
        ws.cell(row=1, column=new_idx, value=col_name)
        headers.append(col_name)
        return new_idx

    # Get the column indices for input, id, output, score, and info columns
    input_idx = headers.index(input_column) + 1
    id_idx = headers.index(id_column) + 1 if id_column in headers else None
    output_idx = ensure_column(output_column)
    score_idx = ensure_column(score_column)
    info_idx = ensure_column(info_column)

    rows_to_process = []

    # Iterate through the rows of the worksheet, starting from the second row (to skip the header), and collect the row indices that meet the criteria for processing
    for r in range(2, ws.max_row + 1):

        # Get the value of the input column for the current row
        cell_val = ws.cell(row=r, column=input_idx).value

        if cell_val is None:
            continue
        if str(cell_val) == '-':
            continue

        # If an id column is specified, check if the id value for the current row is within the specified min and max range. If not, skip this row.
        if id_idx is not None:

            #
            id_val = ws.cell(row=r, column=id_idx).value
            try:
                if id_val is None:
                    continue
                if not (min_id <= float(id_val) <= max_id):
                    continue
            except Exception:
                continue
        rows_to_process.append(r)

    row_count = len(rows_to_process)
    print("Processing rows: ", row_count)

    # Disable printing if the number of rows exceeds 100 to avoid excessive output
    if row_count >= 100:
        printing = False
        print("Disabling printing for over 100 rows")

    updated_rows = 0
    processed_rows = 0

    # Iterate through the rows that need to be processed, and for each row, retrieve the report text, process it using the text processor, and update the worksheet with the required values.
    for r in rows_to_process:

        # Get the row ID and report text for the current row. If the id column is not specified, use the row index (minus 1) as the row ID.
        row_id = ws.cell(row=r, column=id_idx).value if id_idx is not None else r - 1
        report_text = ws.cell(row=r, column=input_idx).value

        if printing:
            display_text = str(report_text)[:200] if report_text is not None else ''
            display_text = display_text.replace("_x000D_", "")
            print(f"Processing row ID: {row_id}, report text: {display_text}...")

        # Process the report text using the text processor, which returns the redacted text, detected words, redacted words, and word types.
        redacted_text, detected_words, redacted_words, word_types = text_processor.process_text(report_text)
        processed_rows += 1

        # If sensitive information is detected, prepare the score and warning message for updating the worksheet. If no sensitive information is detected, set the redacted text to the original report text
        # and clear the warning message and score.
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

        # Update the worksheet with the redacted text, score, and warning message for the current row.
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
    return wb

-- Step 1: Add a new column for rownum
ALTER TABLE report_table ADD COLUMN rownum INTEGER;

-- Step 2: Populate the column with row numbers
WITH cte AS (
  SELECT ROW_NUMBER() OVER (ORDER BY some_ordering_field) AS rownum, rowid
  FROM report_table
)
UPDATE report_table
SET rownum = (SELECT rownum FROM cte WHERE cte.rowid = report_table.rowid);

-- Step 3: Add new columns for anonymized text, score, and info
alter table report_table add column report_anon text;
alter table report_table add column report_anon_score integer;
alter table report_table add column report_anon_info text;

-- Clear the columns if needed to rerun the anonymization process
update report_table set report_anon=null, report_anon_score=null, report_anon_info=null;

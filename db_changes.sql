-- Step 1: Add a new column for rownum
ALTER TABLE thorax_data ADD COLUMN rownum INTEGER;

-- Step 2: Populate the column with row numbers
WITH cte AS (
  SELECT ROW_NUMBER() OVER (ORDER BY PseudoID) AS rownum, rowid
  FROM thorax_data
)
UPDATE thorax_data
SET rownum = (SELECT rownum FROM cte WHERE cte.rowid = thorax_data.rowid);

-- Step 3: Add new columns for anonymized text, score, and info
alter table thorax_data add column report_anon text;
alter table thorax_data add column report_anon_score integer;
alter table thorax_data add column report_anon_info text;

-- Clear the columns if needed to rerun the anonymization process
update thorax_data set report_anon=null, report_anon_score=null, report_anon_info=null, request_anon=null, request_anon_score=null, request_anon_info=null;





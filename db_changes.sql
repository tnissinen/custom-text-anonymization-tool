alter table thorax_data add column report1_anon text;
alter table thorax_data add column report1_anon_score integer;
alter table thorax_data add column report1_anon_info text;

alter table thorax_data add column request1_anon text;
alter table thorax_data add column request1_anon_score integer;
alter table thorax_data add column request1_anon_info text;

alter table thorax_data add column report2_anon text;
alter table thorax_data add column report2_anon_score integer;
alter table thorax_data add column report2_anon_info text;

alter table thorax_data add column request2_anon text;
alter table thorax_data add column request2_anon_score integer;
alter table thorax_data add column request2_anon_info text;

update thorax_data set report1_anon=null, report1_anon_score=null, report1_anon_info=null, request1_anon=null, request1_anon_score=null, request1_anon_info=null;
update thorax_data set report2_anon=null, report2_anon_score=null, report2_anon_info=null, request2_anon=null, request2_anon_score=null, request2_anon_info=null;

-- Next clauses assume(Lausunnot table)

-- Step 1: Add a new column for rownum
ALTER TABLE Lausunnot_10000 ADD COLUMN rownum INTEGER;

-- Step 2: Populate the column with row numbers
WITH cte AS (
  SELECT ROW_NUMBER() OVER (ORDER BY PseudoID) AS rownum, rowid
  FROM Lausunnot_10000
)
UPDATE Lausunnot_10000
SET rownum = (SELECT rownum FROM cte WHERE cte.rowid = Lausunnot_10000.rowid);

create table Lausunnot_Xray_CT_export as select * from Lausunnot_Xray_CT;
create table Lausunnot_10000_export as select * from Lausunnot_10000;

update Lausunnot_Xray_CT_export set PseudoID = 'EXCLUDED';
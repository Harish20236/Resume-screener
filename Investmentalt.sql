CREATE TABLE IF NOT EXISTS master_document_data (
  fund_id UUID PRIMARY KEY,  -- 🔐 Unique record ID for any type of document
  type TEXT CHECK (type IN (
    'email_queue',          -- from processing_queue
    'run_summary',          -- from run_summary
    'manual_case',          -- from manual_case_creation
    'qc_discrepancy',       -- from discrepancy_data
    'fund_mapping',         -- from fund_mapping_aum
    'admin_schedule',       -- from admin_schedule
    'dashboard_metric'      -- from dashboard_metrics
  )),
  parent_id UUID REFERENCES master_document_data(fund_id),  -- 🏗️ Parent-Child Hierarchy
  root_document_id UUID,                                    -- 🔗 Root grouping
  data JSONB,                                               -- 💾 Stores any table's data in flexible format
  created_at TIMESTAMP DEFAULT NOW()
);  


-- 1. Processing Queue (email_queue)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'email_queue',
  '{
    "case_number": "EMAIL-1001",
    "email_subject": "Client Exit Procedure",
    "attachment": true,
    "fund_name": "ABC Growth Fund"
  }'::jsonb
);

-- 2. Run Summary (run_summary)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'run_summary',
  '{
    "duration": "1 week",
    "emails_in_outlook": 50,
    "emails_allocated": 45,
    "emails_unassigned": 5,
    "model_accuracy": 50,
    "model_confidence_score": 50
  }'::jsonb
);

-- 3. Manual Case Creation (manual_case)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'manual_case',
  '{
    "case_number": "CASE-2024-01",
    "priority": "High",
    "activity": "Manual Trigger",
    "attachment": true,
    "status": "Closed"
  }'::jsonb
);

-- 4. Discrepancy Data (qc_discrepancy)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'qc_discrepancy',
  '{
    "fund_name": "1234",
    "investor_id": "5678",
    "investor_name": "KKR",
    "class_id": "qwer",
    "gl_number": "asd",
    "quantity": 100000,
    "price": 10,
    "previous_mv": 50000,
    "post_mv": 100000,
    "percentage_change": 5
  }'::jsonb
);

-- 5. Fund Mapping & AUM (fund_mapping)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'fund_mapping',
  '{
    "fund_name": "XYZ Global Fund",
    "fund_id": "FND-001",
    "series": "Series A",
    "classes": "Class X",
    "common_bw_fm_and_aum": true
  }'::jsonb
);

-- 6. Admin Schedule (admin_schedule)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'admin_schedule',
  '{
    "activity": "Model Schedule",
    "sub_activity": "Mapping",
    "task": "Calendar Sync",
    "model_schedule": "9 AM",
    "username": "Mirza Mehdi Ali",
    "role": "Processor",
    "holiday_calendar": false
  }'::jsonb
);

-- 7. Dashboard Metrics (dashboard_metric)
INSERT INTO master_document_data (fund_id, type, data)
VALUES (
  gen_random_uuid(),
  'dashboard_metric',
  '{
    "request_status": "Closed",
    "model_accuracy": 50,
    "productivity": "Team A - 80%",
    "quality_metrics": "Good"
  }'::jsonb
);  
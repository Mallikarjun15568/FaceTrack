-- Test Attendance Data for January 2026
-- Run this in MySQL to add sample data

-- First check employee IDs
SELECT id, full_name FROM employees LIMIT 5;

-- Add sample attendance for January 2026 (employee_id = 1)
INSERT INTO attendance (employee_id, date, status, check_in_time, check_out_time, working_hours)
VALUES
(1, '2026-01-02', 'present', '2026-01-02 09:00:00', '2026-01-02 17:00:00', 8.0),
(1, '2026-01-03', 'present', '2026-01-03 09:15:00', '2026-01-03 17:30:00', 8.25),
(1, '2026-01-06', 'present', '2026-01-06 09:00:00', '2026-01-06 17:00:00', 8.0),
(1, '2026-01-07', 'present', '2026-01-07 09:00:00', '2026-01-07 17:00:00', 8.0),
(1, '2026-01-08', 'absent', NULL, NULL, 0),
(1, '2026-01-09', 'present', '2026-01-09 09:00:00', '2026-01-09 17:00:00', 8.0),
(1, '2026-01-10', 'present', '2026-01-10 09:00:00', '2026-01-10 17:00:00', 8.0);

-- Verify
SELECT DATE(date) as date, status, working_hours 
FROM attendance 
WHERE YEAR(date) = 2026 AND MONTH(date) = 1 
ORDER BY date;

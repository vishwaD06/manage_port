-- ============================================================================
-- DEMONSTRATION QUERIES FOR DBMS VIVA & EVALUATION
-- Course Project: Smart Food Waste Reduction & Donation Management System
-- Database: food_waste_management
-- Description: 15+ Advanced SQL Queries showcasing relational operations, joins,
--              aggregations, subqueries, grouping, views, and business intelligence.
-- ============================================================================

USE food_waste_management;

-- ----------------------------------------------------------------------------
-- QUERY 1: Multi-Table INNER JOIN (Donation, Donor Details)
-- Concept: INNER JOIN between DONATION and USER to list all food donations with
--          donor contact details and location.
-- Viva Explanation: Retrieves only donations with valid corresponding donor records.
-- ----------------------------------------------------------------------------
SELECT 
    d.Donation_ID,
    d.Food_Type,
    d.Quantity,
    d.Unit,
    d.Food_Category,
    d.Status,
    u.Name AS Donor_Name,
    u.Phone AS Donor_Phone,
    u.Email AS Donor_Email,
    d.Pickup_Address
FROM DONATION d
INNER JOIN `USER` u ON d.User_ID = u.User_ID
ORDER BY d.Donation_Time DESC;

-- Expected Sample Result:
-- +-------------+------------------------------------+----------+------+---------------+-----------+----------------------------------+-----------------+
-- | Donation_ID | Food_Type                          | Quantity | Unit | Food_Category | Status    | Donor_Name                       | Donor_Phone     |
-- +-------------+------------------------------------+----------+------+---------------+-----------+----------------------------------+-----------------+
-- | 1           | Cooked Vegetable Biryani & Raita   | 45.00    | kg   | Cooked Food   | Available | Green Leaf Restaurant & Banquets | +91 98765 11002 |
-- | 2           | Fresh Artisan Sourdough Loaves     | 35.00    | kg   | Bakery        | Available | Sunburst Artisan Bakery          | +91 98765 11004 |
-- +-------------+------------------------------------+----------+------+---------------+-----------+----------------------------------+-----------------+


-- ----------------------------------------------------------------------------
-- QUERY 2: Multi-Table LEFT OUTER JOIN (Donations & Claiming NGOs)
-- Concept: LEFT JOIN ensuring all donations appear even if unclaimed (Claimed_By_NGO_ID IS NULL).
-- Viva Explanation: Demonstrates difference between inner and outer joins in real business context.
-- ----------------------------------------------------------------------------
SELECT 
    d.Donation_ID,
    d.Food_Type,
    d.Quantity,
    d.Status,
    COALESCE(ngo.NGO_Name, 'Unclaimed / Available') AS Claimed_By,
    COALESCE(ngo.Contact_No, 'N/A') AS NGO_Contact,
    COALESCE(ngo.NGO_Type, 'N/A') AS Organization_Type
FROM DONATION d
LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
ORDER BY d.Status, d.Donation_ID;


-- ----------------------------------------------------------------------------
-- QUERY 3: 4-Way Complex JOIN (Donation + Donor + NGO + Pickup + Review)
-- Concept: Complete end-to-end traceability of completed donations.
-- ----------------------------------------------------------------------------
SELECT 
    d.Donation_ID,
    d.Food_Type,
    d.Quantity,
    donor.Name AS Donor_Business,
    ngo.NGO_Name AS Beneficiary_NGO,
    p.Driver_Name,
    p.Vehicle_No,
    r.Rating,
    r.Comment AS Review_Feedback
FROM DONATION d
JOIN `USER` donor ON d.User_ID = donor.User_ID
JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
LEFT JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
WHERE d.Status = 'Completed';


-- ----------------------------------------------------------------------------
-- QUERY 4: Aggregation with GROUP BY (Total Rescued Food by Category)
-- Concept: SUM, COUNT, and AVG grouped by category for inventory analysis.
-- ----------------------------------------------------------------------------
SELECT 
    Food_Category,
    COUNT(Donation_ID) AS Total_Donation_Lots,
    SUM(Quantity) AS Total_Rescued_Weight_Kg,
    ROUND(AVG(Quantity), 2) AS Avg_Batch_Size_Kg,
    MIN(Quantity) AS Smallest_Donation_Kg,
    MAX(Quantity) AS Largest_Donation_Kg
FROM DONATION
GROUP BY Food_Category
ORDER BY Total_Rescued_Weight_Kg DESC;


-- ----------------------------------------------------------------------------
-- QUERY 5: Aggregation with GROUP BY and HAVING Clause
-- Concept: Filter aggregated groups where the total input processing load exceeds 300 kg.
-- Viva Explanation: HAVING filters aggregated groups, unlike WHERE which filters individual rows.
-- ----------------------------------------------------------------------------
SELECT 
    c.Center_ID,
    c.Center_Name,
    c.Center_Type,
    COUNT(p.Process_ID) AS Total_Processes,
    SUM(p.Input_Quantity) AS Total_Input_Waste_Kg,
    SUM(p.Output_Quantity) AS Total_Resource_Yield_Kg
FROM COLLECTION_CENTER c
JOIN PROCESS p ON c.Center_ID = p.Center_ID
GROUP BY c.Center_ID, c.Center_Name, c.Center_Type
HAVING SUM(p.Input_Quantity) > 300.00
ORDER BY Total_Input_Waste_Kg DESC;


-- ----------------------------------------------------------------------------
-- QUERY 6: Nested Subquery using IN Operator
-- Concept: Identify all Donors who have made donations that achieved a 5-Star rating.
-- ----------------------------------------------------------------------------
SELECT 
    User_ID,
    Name AS Donor_Name,
    Email,
    Phone,
    Address
FROM `USER`
WHERE User_ID IN (
    SELECT DISTINCT d.User_ID
    FROM DONATION d
    JOIN REVIEW r ON d.Donation_ID = r.Donation_ID
    WHERE r.Rating = 5
);


-- ----------------------------------------------------------------------------
-- QUERY 7: Subquery using NOT EXISTS / Correlated Subquery
-- Concept: Find NGOs registered in the system that have NOT claimed any food donation yet.
-- Viva Explanation: Crucial for outreach to identify under-served or inactive NGO partners.
-- ----------------------------------------------------------------------------
SELECT 
    n.NGO_ID,
    n.NGO_Name,
    n.NGO_Type,
    n.Contact_No,
    n.Email
FROM NGO_RECEIVER n
WHERE NOT EXISTS (
    SELECT 1 
    FROM DONATION d 
    WHERE d.Claimed_By_NGO_ID = n.NGO_ID
);


-- ----------------------------------------------------------------------------
-- QUERY 8: Correlated Subquery comparing Against Category Average
-- Concept: Find donations whose quantity is greater than the average quantity
--          of donations within that same food category.
-- ----------------------------------------------------------------------------
SELECT 
    d1.Donation_ID,
    d1.Food_Type,
    d1.Food_Category,
    d1.Quantity,
    ROUND((
        SELECT AVG(d2.Quantity)
        FROM DONATION d2
        WHERE d2.Food_Category = d1.Food_Category
    ), 2) AS Category_Avg_Quantity
FROM DONATION d1
WHERE d1.Quantity > (
    SELECT AVG(d2.Quantity)
    FROM DONATION d2
    WHERE d2.Food_Category = d1.Food_Category
)
ORDER BY d1.Food_Category, d1.Quantity DESC;


-- ----------------------------------------------------------------------------
-- QUERY 9: Executive KPI Aggregation (System-Wide Dashboard Metrics)
-- Concept: Single-query aggregation computing active KPIs across multiple tables.
-- ----------------------------------------------------------------------------
SELECT 
    (SELECT COUNT(*) FROM `USER` WHERE User_Type = 'Donor') AS Total_Donors,
    (SELECT COUNT(*) FROM `NGO_RECEIVER`) AS Total_Registered_NGOs,
    (SELECT COUNT(*) FROM `DONATION`) AS Total_Donations_Listed,
    (SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Available') AS Available_Donations,
    (SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Completed') AS Completed_Donations,
    (SELECT COALESCE(SUM(Quantity), 0) FROM `DONATION` WHERE Status = 'Completed') AS Total_Rescued_Food_Kg,
    (SELECT COALESCE(SUM(Quantity), 0) FROM `WASTE_ITEM`) AS Total_Waste_Recorded_Kg,
    (SELECT COALESCE(SUM(Output_Quantity), 0) FROM `PROCESS` WHERE Status = 'Completed') AS Total_Recycled_Output_Kg,
    ROUND((SELECT COUNT(*) FROM `DONATION` WHERE Status = 'Completed') / 
          (SELECT GREATEST(COUNT(*), 1) FROM `DONATION`) * 100, 2) AS Donation_Success_Rate_Pct;


-- ----------------------------------------------------------------------------
-- QUERY 10: Date/Time Arithmetic and Expiry Warning Logic
-- Concept: Identify food expiring within the next 24 hours that needs urgent dispatch.
-- ----------------------------------------------------------------------------
SELECT 
    Donation_ID,
    Food_Type,
    Food_Category,
    Quantity,
    Unit,
    Expiry_Date,
    NOW() AS Current_System_Time,
    TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) AS Hours_Remaining,
    CASE 
        WHEN TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) <= 6 THEN 'CRITICAL: Expiring in < 6 hrs'
        WHEN TIMESTAMPDIFF(HOUR, NOW(), Expiry_Date) <= 24 THEN 'WARNING: Expiring within 24 hrs'
        ELSE 'SAFE'
    END AS Urgency_Level
FROM DONATION
WHERE Status = 'Available' AND Expiry_Date > NOW()
ORDER BY Expiry_Date ASC;


-- ----------------------------------------------------------------------------
-- QUERY 11: Eco-Conversion Efficiency by Process Type (Compost / Biogas / Recycle)
-- Concept: Calculate aggregate yield ratio (Output / Input) per processing method.
-- ----------------------------------------------------------------------------
SELECT 
    Process_Type,
    COUNT(Process_ID) AS Total_Runs,
    SUM(Input_Quantity) AS Total_Waste_Diverted_Kg,
    SUM(Output_Quantity) AS Total_Useful_Output,
    ROUND((SUM(Output_Quantity) / NULLIF(SUM(Input_Quantity), 0)) * 100, 2) AS Conversion_Efficiency_Percentage
FROM PROCESS
WHERE Status = 'Completed'
GROUP BY Process_Type
ORDER BY Conversion_Efficiency_Percentage DESC;


-- ----------------------------------------------------------------------------
-- QUERY 12: Collection Center Capacity Utilization Percentage
-- Concept: Mathematical computation on table attributes to identify overload risk.
-- ----------------------------------------------------------------------------
SELECT 
    Center_ID,
    Center_Name,
    Center_Type,
    Capacity AS Max_Capacity_Kg,
    Current_Occupancy AS Current_Waste_Load_Kg,
    ROUND((Current_Occupancy / Capacity) * 100, 2) AS Utilization_Percentage,
    CASE 
        WHEN (Current_Occupancy / Capacity) >= 0.85 THEN 'CRITICAL OVERLOAD RISK'
        WHEN (Current_Occupancy / Capacity) >= 0.50 THEN 'MODERATE LOAD'
        ELSE 'OPTIMAL / LOW LOAD'
    END AS Hub_Status
FROM COLLECTION_CENTER
ORDER BY Utilization_Percentage DESC;


-- ----------------------------------------------------------------------------
-- QUERY 13: Donor Ranking using Window Function (DENSE_RANK)
-- Concept: SQL Window function to rank donors by volume of food saved.
-- ----------------------------------------------------------------------------
SELECT 
    u.User_ID,
    u.Name AS Donor_Name,
    COUNT(d.Donation_ID) AS Donations_Count,
    SUM(d.Quantity) AS Total_Food_Donated_Kg,
    DENSE_RANK() OVER (ORDER BY SUM(d.Quantity) DESC) AS Donor_Rank
FROM `USER` u
JOIN DONATION d ON u.User_ID = d.User_ID
WHERE u.User_Type = 'Donor'
GROUP BY u.User_ID, u.Name
ORDER BY Donor_Rank ASC;


-- ----------------------------------------------------------------------------
-- QUERY 14: Querying Database View with Compound Conditions
-- Concept: Instant query execution on `vw_available_donations` view.
-- ----------------------------------------------------------------------------
SELECT 
    Donation_ID,
    Food_Type,
    Quantity,
    Donor_Name,
    Donor_Phone,
    Pickup_Address,
    Hours_Until_Expiry
FROM vw_available_donations
WHERE Food_Category IN ('Cooked Food', 'Bakery')
  AND Hours_Until_Expiry > 0
ORDER BY Hours_Until_Expiry ASC;


-- ----------------------------------------------------------------------------
-- QUERY 15: Transaction & Rollback Demonstration (ACID Properties)
-- Concept: Demonstrates atomic operations and rollback when an integrity error occurs.
-- Viva Explanation: Ensures database never enters an inconsistent state if a step fails.
-- ----------------------------------------------------------------------------
-- Scenario: NGO requests cancellation of a scheduled pickup, resetting donation to 'Available'.
START TRANSACTION;

-- Step A: Cancel the pickup
UPDATE PICKUP 
SET Status = 'Cancelled', Notes = CONCAT(COALESCE(Notes, ''), ' | Cancelled by logistics coordinator.')
WHERE Donation_ID = 6;

-- Step B: Reset the donation status back to Available and clear the claimed NGO
UPDATE DONATION 
SET Status = 'Available', Claimed_By_NGO_ID = NULL 
WHERE Donation_ID = 6;

-- Verification query within transaction
SELECT Donation_ID, Status, Claimed_By_NGO_ID FROM DONATION WHERE Donation_ID = 6;
SELECT Pickup_ID, Donation_ID, Status FROM PICKUP WHERE Donation_ID = 6;

-- Either commit or rollback:
-- COMMIT; -- (Uncomment in production to persist)
ROLLBACK;   -- (Rollback preserves original demonstration state)


-- ----------------------------------------------------------------------------
-- QUERY 16: NGO to Collection Center Routing (<DELIVERS TO> Relationship)
-- Concept: Verifies which Collection Center each certified NGO delivers collected items
--          to as explicitly specified in the canonical ER Diagram.
-- Viva Explanation: Demonstrates the <DELIVERS TO> relationship linking NGO_RECEIVER [N]
--                   to COLLECTION_CENTER [1] for municipal triage and excess redistribution.
-- ----------------------------------------------------------------------------
SELECT 
    n.NGO_ID,
    n.NGO_Name,
    n.NGO_Type,
    n.License_No,
    n.Contact_No,
    c.Center_ID,
    c.Center_Name AS Triage_Collection_Center,
    c.Center_Type AS Center_Classification,
    c.Address AS Center_Location
FROM NGO_RECEIVER n
LEFT JOIN COLLECTION_CENTER c ON n.Delivers_To_Center_ID = c.Center_ID
ORDER BY n.NGO_Name;

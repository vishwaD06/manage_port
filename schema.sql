-- ============================================================================
-- DATABASE SCHEMA: Smart Food Waste Reduction & Donation Management System
-- Database Engine: MySQL / MariaDB (InnoDB Storage Engine)
-- Target Database: food_waste_management
-- Normalization: Fully normalized to 3NF
-- ============================================================================

DROP DATABASE IF EXISTS food_waste_management;
CREATE DATABASE food_waste_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_waste_management;

SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------------------------------------------------------
-- 1. Table: USER
-- Conceptual Entity: All system actors (Donors, NGOs, Recyclers, Admins)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `USER`;
CREATE TABLE `USER` (
    `User_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Name` VARCHAR(100) NOT NULL,
    `Phone` VARCHAR(20) NOT NULL,
    `Email` VARCHAR(100) NOT NULL UNIQUE,
    `Password` VARCHAR(255) NOT NULL,
    `Address` TEXT NOT NULL,
    `User_Type` ENUM('Donor', 'NGO/Receiver', 'Recycler', 'Admin') NOT NULL,
    `Date_Joined` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_user_type` (`User_Type`),
    INDEX `idx_user_email` (`Email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Table: NGO_RECEIVER
-- Conceptual Entity: Certified NGOs, Charities, Shelters receiving food
-- Relation: 1-to-1 extension of USER where User_Type = 'NGO/Receiver'
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `NGO_RECEIVER`;
CREATE TABLE `NGO_RECEIVER` (
    `NGO_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `User_ID` INT NOT NULL UNIQUE,
    `Delivers_To_Center_ID` INT NULL COMMENT 'FK to COLLECTION_CENTER (ER Relationship: DELIVERS TO)',
    `NGO_Name` VARCHAR(150) NOT NULL,
    `Address` TEXT NOT NULL,
    `Contact_No` VARCHAR(20) NOT NULL,
    `License_No` VARCHAR(50) NOT NULL UNIQUE,
    `NGO_Type` VARCHAR(50) NOT NULL COMMENT 'NGO, Charity, Shelter, Food Bank',
    `Email` VARCHAR(100) NOT NULL,
    `Website` VARCHAR(150) DEFAULT 'https://foodrescue.ngo',
    CONSTRAINT `fk_ngo_user` FOREIGN KEY (`User_ID`) REFERENCES `USER` (`User_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_ngo_center` FOREIGN KEY (`Delivers_To_Center_ID`) REFERENCES `COLLECTION_CENTER` (`Center_ID`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Table: COLLECTION_CENTER
-- Conceptual Entity: Municipal & logistics hubs managing food/waste triage
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `COLLECTION_CENTER`;
CREATE TABLE `COLLECTION_CENTER` (
    `Center_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Center_Name` VARCHAR(150) NOT NULL,
    `Address` TEXT NOT NULL,
    `Contact_No` VARCHAR(20) NOT NULL,
    `Capacity` DECIMAL(10,2) NOT NULL COMMENT 'Storage capacity in kg',
    `Current_Occupancy` DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT 'Current waste stored in kg',
    `Center_Type` VARCHAR(50) NOT NULL,
    `Latitude` DECIMAL(10, 6) DEFAULT 18.520430 COMMENT 'Geo Latitude (Pune)',
    `Longitude` DECIMAL(10, 6) DEFAULT 73.856744 COMMENT 'Geo Longitude (Pune)',
    INDEX `idx_center_type` (`Center_Type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Table: DONATION
-- Conceptual Entity: Surplus food listings posted by Donors
-- Relationships: Many Donations made by 1 User (Donor)
--                1 Donation claimed by 0 or 1 NGO_RECEIVER
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `DONATION`;
CREATE TABLE `DONATION` (
    `Donation_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `User_ID` INT NOT NULL COMMENT 'FK to USER (Donor)',
    `Claimed_By_NGO_ID` INT NULL COMMENT 'FK to NGO_RECEIVER who claimed this',
    `Food_Type` VARCHAR(120) NOT NULL,
    `Quantity` DECIMAL(10,2) NOT NULL,
    `Unit` VARCHAR(20) NOT NULL DEFAULT 'kg',
    `Packaging_Type` VARCHAR(80) NOT NULL,
    `Pickup_Address` TEXT NOT NULL,
    `Food_Category` ENUM('Cooked Food', 'Raw Groceries', 'Bakery', 'Fruits & Vegetables', 'Packaged/Canned', 'Veg', 'Non-Veg', 'Vegetarian', 'Non-Vegetarian', 'Cooked Food (Veg)', 'Cooked Food (Non-Veg)') NOT NULL COMMENT 'Categorization matching ER Diagram (Veg/Non-Veg)',
    `Prepared_On` DATETIME NOT NULL,
    `Expiry_Date` DATETIME NOT NULL,
    `Status` ENUM('Available', 'Claimed', 'Scheduled', 'Picked', 'Completed', 'Cancelled', 'Expired') NOT NULL DEFAULT 'Available',
    `Safety_Status` ENUM('Verified Safe', 'Caution Required', 'Diverted to Waste', 'Pending Inspection') NOT NULL DEFAULT 'Verified Safe' COMMENT 'FSSAI & Municipal Food Safety Inspection Protocol',
    `Temperature_Celsius` DECIMAL(4,1) NOT NULL DEFAULT 65.0 COMMENT 'Holding/dispatch temperature in C',
    `Safety_Inspector` VARCHAR(100) NOT NULL DEFAULT 'PMC Certified Food Safety Officer',
    `Safety_Notes` TEXT NULL COMMENT 'Sensory, temperature, and packaging compliance remarks',
    `Donation_Time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_donation_user` FOREIGN KEY (`User_ID`) REFERENCES `USER` (`User_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_donation_ngo` FOREIGN KEY (`Claimed_By_NGO_ID`) REFERENCES `NGO_RECEIVER` (`NGO_ID`) ON DELETE SET NULL,
    INDEX `idx_donation_status` (`Status`),
    INDEX `idx_donation_category` (`Food_Category`),
    INDEX `idx_donation_expiry` (`Expiry_Date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. Table: PICKUP
-- Conceptual Entity: Scheduled transport and driver details for food donations
-- Relationships: 1-to-1 with DONATION, Many Pickups coordinated via Center
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `PICKUP`;
CREATE TABLE `PICKUP` (
    `Pickup_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Donation_ID` INT NOT NULL UNIQUE,
    `Center_ID` INT NULL,
    `Pickup_Time` DATETIME NOT NULL,
    `Vehicle_No` VARCHAR(30) NOT NULL,
    `Driver_Name` VARCHAR(100) NOT NULL,
    `Notes` TEXT,
    `Status` ENUM('Scheduled', 'In Transit', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Scheduled',
    `Completed_At` DATETIME NULL,
    CONSTRAINT `fk_pickup_donation` FOREIGN KEY (`Donation_ID`) REFERENCES `DONATION` (`Donation_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_pickup_center` FOREIGN KEY (`Center_ID`) REFERENCES `COLLECTION_CENTER` (`Center_ID`) ON DELETE SET NULL,
    INDEX `idx_pickup_status` (`Status`),
    INDEX `idx_pickup_time` (`Pickup_Time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 6. Table: REPORT (Created before Waste Item to support relational linkage)
-- Conceptual Entity: Formal audits and analytics reports
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `REPORT`;
CREATE TABLE `REPORT` (
    `Report_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Center_ID` INT NULL,
    `Generated_By_User_ID` INT NOT NULL,
    `Report_Type` ENUM('Daily', 'Monthly', 'Yearly', 'Daily Log', 'Monthly Summary', 'Donation Audit', 'Waste Processing', 'Annual Impact') NOT NULL COMMENT 'Matches ER Diagram (Daily/Monthly/Yearly)',
    `Start_Date` DATE NOT NULL,
    `End_Date` DATE NOT NULL,
    `Generated_On` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `Summary` TEXT NOT NULL,
    CONSTRAINT `fk_report_center` FOREIGN KEY (`Center_ID`) REFERENCES `COLLECTION_CENTER` (`Center_ID`) ON DELETE SET NULL,
    CONSTRAINT `fk_report_user` FOREIGN KEY (`Generated_By_User_ID`) REFERENCES `USER` (`User_ID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 7. Table: WASTE_ITEM
-- Conceptual Entity: Inedible surplus or spoiled goods logged at centers
-- Design Note: The ER diagram labels the primary identifier Report_ID. To ensure
--              proper 3NF normalization without key collisions with the REPORT entity,
--              this table uses Waste_ID as PK while retaining Center_ID & Report_ID FKs.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `WASTE_ITEM`;
CREATE TABLE `WASTE_ITEM` (
    `Waste_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Center_ID` INT NOT NULL,
    `Report_ID` INT NULL,
    `Waste_Type` ENUM('Food', 'Organic', 'Inorganic', 'Expired Food Scraps', 'Organic Kitchen Waste', 'Spoiled Produce', 'Packaging / Inorganics', 'Biomass Residue') NOT NULL COMMENT 'Matches ER Diagram (Food/Organic/Inorganic)',
    `Quantity` DECIMAL(10,2) NOT NULL,
    `Unit` VARCHAR(20) NOT NULL DEFAULT 'kg',
    `Description` TEXT,
    `Recorded_Date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `Status` ENUM('Pending', 'In Processing', 'Processed', 'Disposed') NOT NULL DEFAULT 'Pending',
    CONSTRAINT `fk_waste_center` FOREIGN KEY (`Center_ID`) REFERENCES `COLLECTION_CENTER` (`Center_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_waste_report` FOREIGN KEY (`Report_ID`) REFERENCES `REPORT` (`Report_ID`) ON DELETE SET NULL,
    INDEX `idx_waste_center` (`Center_ID`),
    INDEX `idx_waste_status` (`Status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 8. Table: PROCESS
-- Conceptual Entity: Ecological treatment runs (Composting, Recycling, Biogas)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `PROCESS`;
CREATE TABLE `PROCESS` (
    `Process_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Center_ID` INT NOT NULL,
    `Waste_ID` INT NULL,
    `Process_Type` ENUM('Composting', 'Recycler', 'Recycling', 'Biogas') NOT NULL COMMENT 'Matches ER Diagram (Composting/Recycler/Biogas)',
    `Start_Date` DATETIME NOT NULL,
    `End_Date` DATETIME NULL,
    `Input_Quantity` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `Output_Quantity` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `Remarks` TEXT,
    `Status` ENUM('Initiated', 'In Progress', 'Completed') NOT NULL DEFAULT 'Initiated',
    CONSTRAINT `fk_process_center` FOREIGN KEY (`Center_ID`) REFERENCES `COLLECTION_CENTER` (`Center_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_process_waste` FOREIGN KEY (`Waste_ID`) REFERENCES `WASTE_ITEM` (`Waste_ID`) ON DELETE SET NULL,
    INDEX `idx_process_type` (`Process_Type`),
    INDEX `idx_process_status` (`Status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 9. Table: REVIEW
-- Conceptual Entity: Quality and trust evaluations on completed food donations
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `REVIEW`;
CREATE TABLE `REVIEW` (
    `Review_ID` INT AUTO_INCREMENT PRIMARY KEY,
    `Donation_ID` INT NOT NULL,
    `User_ID` INT NOT NULL,
    `Rating` INT NOT NULL CHECK (`Rating` >= 1 AND `Rating` <= 5),
    `Comment` TEXT NOT NULL,
    `Review_Date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_review_donation` FOREIGN KEY (`Donation_ID`) REFERENCES `DONATION` (`Donation_ID`) ON DELETE CASCADE,
    CONSTRAINT `fk_review_user` FOREIGN KEY (`User_ID`) REFERENCES `USER` (`User_ID`) ON DELETE CASCADE,
    CONSTRAINT `uk_donation_user_review` UNIQUE (`Donation_ID`, `User_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- DATABASE VIEWS FOR APPLICATION REPORTING AND PERFORMANCE
-- ============================================================================

-- View 1: Available active donations with hours until expiry
DROP VIEW IF EXISTS `vw_available_donations`;
CREATE VIEW `vw_available_donations` AS
SELECT 
    d.Donation_ID,
    d.User_ID AS Donor_ID,
    u.Name AS Donor_Name,
    u.Phone AS Donor_Phone,
    u.Email AS Donor_Email,
    d.Food_Type,
    d.Quantity,
    d.Unit,
    d.Packaging_Type,
    d.Pickup_Address,
    d.Food_Category,
    d.Expiry_Date,
    d.Prepared_On,
    d.Status,
    d.Donation_Time,
    TIMESTAMPDIFF(HOUR, NOW(), d.Expiry_Date) AS Hours_Until_Expiry
FROM DONATION d
JOIN USER u ON d.User_ID = u.User_ID
WHERE d.Status = 'Available' AND d.Expiry_Date > NOW();

-- View 2: Complete donation summary with donor, NGO, pickup, and review
DROP VIEW IF EXISTS `vw_donation_summary`;
CREATE VIEW `vw_donation_summary` AS
SELECT 
    d.Donation_ID,
    d.Food_Type,
    d.Quantity,
    d.Unit,
    d.Food_Category,
    d.Status,
    d.Donation_Time,
    d.Expiry_Date,
    donor.User_ID AS Donor_ID,
    donor.Name AS Donor_Name,
    donor.Email AS Donor_Email,
    ngo.NGO_ID,
    ngo.NGO_Name,
    ngo.Contact_No AS NGO_Contact,
    p.Pickup_ID,
    p.Pickup_Time,
    p.Status AS Pickup_Status,
    p.Vehicle_No,
    p.Driver_Name,
    r.Review_ID,
    r.Rating,
    r.Comment AS Review_Comment,
    r.Review_Date
FROM DONATION d
JOIN USER donor ON d.User_ID = donor.User_ID
LEFT JOIN NGO_RECEIVER ngo ON d.Claimed_By_NGO_ID = ngo.NGO_ID
LEFT JOIN PICKUP p ON d.Donation_ID = p.Donation_ID
LEFT JOIN REVIEW r ON d.Donation_ID = r.Donation_ID;

-- View 3: Collection Center operational analytics
DROP VIEW IF EXISTS `vw_center_analytics`;
CREATE VIEW `vw_center_analytics` AS
SELECT 
    c.Center_ID,
    c.Center_Name,
    c.Address,
    c.Contact_No,
    c.Center_Type,
    c.Capacity,
    c.Current_Occupancy,
    c.Latitude,
    c.Longitude,
    ROUND((c.Current_Occupancy / c.Capacity) * 100, 2) AS Utilization_Percentage,
    COALESCE(SUM(w.Quantity), 0) AS Total_Waste_Logged,
    COUNT(DISTINCT p.Process_ID) AS Total_Processes_Run,
    COALESCE(SUM(p.Output_Quantity), 0) AS Total_Processing_Output
FROM COLLECTION_CENTER c
LEFT JOIN WASTE_ITEM w ON c.Center_ID = w.Center_ID
LEFT JOIN PROCESS p ON c.Center_ID = p.Center_ID
GROUP BY c.Center_ID, c.Center_Name, c.Address, c.Contact_No, c.Center_Type, c.Capacity, c.Current_Occupancy, c.Latitude, c.Longitude;

-- ============================================================================
-- TRIGGERS FOR BUSINESS RULE ENFORCEMENT & AUDITING
-- ============================================================================

DELIMITER $$

-- Trigger 1: Increment Collection Center occupancy when new waste is logged
DROP TRIGGER IF EXISTS `trg_waste_insert_occupancy`$$
CREATE TRIGGER `trg_waste_insert_occupancy`
AFTER INSERT ON `WASTE_ITEM`
FOR EACH ROW
BEGIN
    IF NEW.Status IN ('Pending', 'In Processing') THEN
        UPDATE `COLLECTION_CENTER`
        SET `Current_Occupancy` = LEAST(`Capacity`, `Current_Occupancy` + NEW.Quantity)
        WHERE `Center_ID` = NEW.Center_ID;
    END IF;
END$$

-- Trigger 2: Decrement Collection Center occupancy when waste is processed or disposed
DROP TRIGGER IF EXISTS `trg_waste_update_occupancy`$$
CREATE TRIGGER `trg_waste_update_occupancy`
AFTER UPDATE ON `WASTE_ITEM`
FOR EACH ROW
BEGIN
    IF OLD.Status IN ('Pending', 'In Processing') AND NEW.Status IN ('Processed', 'Disposed') THEN
        UPDATE `COLLECTION_CENTER`
        SET `Current_Occupancy` = GREATEST(0, `Current_Occupancy` - OLD.Quantity)
        WHERE `Center_ID` = NEW.Center_ID;
    END IF;
END$$

-- Trigger 3: Automatically set DONATION status to 'Completed' when PICKUP is completed
DROP TRIGGER IF EXISTS `trg_pickup_complete_donation`$$
CREATE TRIGGER `trg_pickup_complete_donation`
AFTER UPDATE ON `PICKUP`
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Completed' AND OLD.Status <> 'Completed' THEN
        UPDATE `DONATION`
        SET `Status` = 'Completed'
        WHERE `Donation_ID` = NEW.Donation_ID;
    END IF;
END$$

-- ============================================================================
-- STORED PROCEDURES FOR TRANSACTIONAL OPERATIONS
-- ============================================================================

-- Stored Procedure 1: Atomically claim a donation and schedule pickup
DROP PROCEDURE IF EXISTS `sp_claim_and_schedule_pickup`$$
CREATE PROCEDURE `sp_claim_and_schedule_pickup`(
    IN p_donation_id INT,
    IN p_ngo_id INT,
    IN p_pickup_time DATETIME,
    IN p_vehicle_no VARCHAR(30),
    IN p_driver_name VARCHAR(100),
    IN p_notes TEXT,
    IN p_center_id INT
)
BEGIN
    DECLARE v_curr_status VARCHAR(20);
    DECLARE v_expiry DATETIME;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lock and check current donation status
    SELECT Status, Expiry_Date INTO v_curr_status, v_expiry
    FROM DONATION
    WHERE Donation_ID = p_donation_id
    FOR UPDATE;

    IF v_curr_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Donation record does not exist.';
    ELSEIF v_curr_status <> 'Available' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Donation is no longer available.';
    ELSEIF v_expiry < NOW() THEN
        UPDATE DONATION SET Status = 'Expired' WHERE Donation_ID = p_donation_id;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Error: Food donation has expired.';
    ELSE
        -- 1. Update Donation with claiming NGO and status
        UPDATE DONATION
        SET Claimed_By_NGO_ID = p_ngo_id,
            Status = 'Scheduled'
        WHERE Donation_ID = p_donation_id;

        -- 2. Insert or update Pickup entry
        INSERT INTO PICKUP (Donation_ID, Center_ID, Pickup_Time, Vehicle_No, Driver_Name, Notes, Status)
        VALUES (p_donation_id, p_center_id, p_pickup_time, p_vehicle_no, p_driver_name, p_notes, 'Scheduled')
        ON DUPLICATE KEY UPDATE
            Center_ID = p_center_id,
            Pickup_Time = p_pickup_time,
            Vehicle_No = p_vehicle_no,
            Driver_Name = p_driver_name,
            Notes = p_notes,
            Status = 'Scheduled';

        COMMIT;
    END IF;
END$$

-- Stored Procedure 2: Atomically log a waste processing conversion run
DROP PROCEDURE IF EXISTS `sp_record_waste_processing`$$
CREATE PROCEDURE `sp_record_waste_processing`(
    IN p_center_id INT,
    IN p_waste_id INT,
    IN p_process_type VARCHAR(30),
    IN p_start_date DATETIME,
    IN p_end_date DATETIME,
    IN p_input_qty DECIMAL(10,2),
    IN p_output_qty DECIMAL(10,2),
    IN p_remarks TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- 1. Insert Process execution record
    INSERT INTO PROCESS (Center_ID, Waste_ID, Process_Type, Start_Date, End_Date, Input_Quantity, Output_Quantity, Remarks, Status)
    VALUES (p_center_id, p_waste_id, p_process_type, p_start_date, p_end_date, p_input_qty, p_output_qty, p_remarks, 'Completed');

    -- 2. Mark the waste item as Processed if linked
    IF p_waste_id IS NOT NULL THEN
        UPDATE WASTE_ITEM
        SET Status = 'Processed'
        WHERE Waste_ID = p_waste_id;
    END IF;

    COMMIT;
END$$

DELIMITER ;

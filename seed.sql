-- ============================================================================
-- SEED DATA: Smart Food Waste Reduction & Donation Management System
-- Purpose: Realistic sample data demonstrating all roles, statuses, and queries
-- ============================================================================

USE food_waste_management;

SET FOREIGN_KEY_CHECKS = 0;

-- Clean existing data
TRUNCATE TABLE `REVIEW`;
TRUNCATE TABLE `PROCESS`;
TRUNCATE TABLE `WASTE_ITEM`;
TRUNCATE TABLE `REPORT`;
TRUNCATE TABLE `PICKUP`;
TRUNCATE TABLE `DONATION`;
TRUNCATE TABLE `COLLECTION_CENTER`;
TRUNCATE TABLE `NGO_RECEIVER`;
TRUNCATE TABLE `USER`;

-- ----------------------------------------------------------------------------
-- 1. Insert USERS (Password hashed with scrypt/werkzeug)
-- Password for admin accounts: admin123
-- Password for donor accounts: donor123
-- Password for ngo accounts: ngo123
-- Password for recycler accounts: recycler123
-- ----------------------------------------------------------------------------
INSERT INTO `USER` (`User_ID`, `Name`, `Phone`, `Email`, `Password`, `Address`, `User_Type`, `Date_Joined`) VALUES
(1, 'System Administrator', '+91 98765 00001', 'admin@foodwaste.org', 'scrypt:32768:8:1$K8EYLl6NIIDZ5CGO$54e26b066dbbf349c989f6042020acfe14446fbf3997e12c22a1f0f398063797fece969f935639df581783aa17d23a04abbe63d8b9b3920a4993e8f1c39f9e78', 'Municipal Corp HQ, Civic Center, Tech City', 'Admin', DATE_SUB(NOW(), INTERVAL 90 DAY)),
(2, 'Green Leaf Restaurant & Banquets', '+91 98765 11002', 'donor.greenleaf@gmail.com', 'scrypt:32768:8:1$9roSwpsSwamCKYxW$e570beecb54be74cd3b8bb3240c6de6d79fa9b7283f4183d6223f225d2215b43fbfc25bddfcb2bee511f2486ea02c0de88cf8f59aaf01040d55d7b6dab547df4', 'Shop 12-14, Food Street, Indiranagar', 'Donor', DATE_SUB(NOW(), INTERVAL 60 DAY)),
(3, 'Hyatt Grand Regency Catering', '+91 98765 11003', 'donor.hyatt@gmail.com', 'scrypt:32768:8:1$9roSwpsSwamCKYxW$e570beecb54be74cd3b8bb3240c6de6d79fa9b7283f4183d6223f225d2215b43fbfc25bddfcb2bee511f2486ea02c0de88cf8f59aaf01040d55d7b6dab547df4', 'Sector 4, Ring Road Expressway', 'Donor', DATE_SUB(NOW(), INTERVAL 50 DAY)),
(4, 'Sunburst Artisan Bakery', '+91 98765 11004', 'donor.bakery@gmail.com', 'scrypt:32768:8:1$9roSwpsSwamCKYxW$e570beecb54be74cd3b8bb3240c6de6d79fa9b7283f4183d6223f225d2215b43fbfc25bddfcb2bee511f2486ea02c0de88cf8f59aaf01040d55d7b6dab547df4', '88 Mall Road, Central Market', 'Donor', DATE_SUB(NOW(), INTERVAL 45 DAY)),
(5, 'Fresh Grocers Wholesale Supermarket', '+91 98765 11005', 'donor.grocers@gmail.com', 'scrypt:32768:8:1$9roSwpsSwamCKYxW$e570beecb54be74cd3b8bb3240c6de6d79fa9b7283f4183d6223f225d2215b43fbfc25bddfcb2bee511f2486ea02c0de88cf8f59aaf01040d55d7b6dab547df4', 'Plot 45, APMC Mandi Complex, South Zone', 'Donor', DATE_SUB(NOW(), INTERVAL 40 DAY)),
(6, 'City College Central Mess', '+91 98765 11006', 'donor.college@gmail.com', 'scrypt:32768:8:1$9roSwpsSwamCKYxW$e570beecb54be74cd3b8bb3240c6de6d79fa9b7283f4183d6223f225d2215b43fbfc25bddfcb2bee511f2486ea02c0de88cf8f59aaf01040d55d7b6dab547df4', 'Campus Block C, University Enclave', 'Donor', DATE_SUB(NOW(), INTERVAL 35 DAY)),
(7, 'Hope Feeding Foundation', '+91 98765 22001', 'ngo.hope@charity.org', 'scrypt:32768:8:1$Vk1h3mirSirY4Uyz$981bfedcee215b1966e8552b612aa2ff42a5217c55d73a3935e70aa86f46e99257a1ca04be276b67f6d1452b508ee6be38b88d73b798a32e7d075ae9434d9e03', 'Building 24, Community Care Layout, East Hub', 'NGO/Receiver', DATE_SUB(NOW(), INTERVAL 55 DAY)),
(8, 'Smiles Shelter & Care Home', '+91 98765 22002', 'ngo.smiles@shelter.org', 'scrypt:32768:8:1$Vk1h3mirSirY4Uyz$981bfedcee215b1966e8552b612aa2ff42a5217c55d73a3935e70aa86f46e99257a1ca04be276b67f6d1452b508ee6be38b88d73b798a32e7d075ae9434d9e03', 'Near Ashoka Pillar, Old Cantonment', 'NGO/Receiver', DATE_SUB(NOW(), INTERVAL 48 DAY)),
(9, 'Annapurna Hunger Relief Mission', '+91 98765 22003', 'ngo.annapurna@relief.org', 'scrypt:32768:8:1$Vk1h3mirSirY4Uyz$981bfedcee215b1966e8552b612aa2ff42a5217c55d73a3935e70aa86f46e99257a1ca04be276b67f6d1452b508ee6be38b88d73b798a32e7d075ae9434d9e03', 'Sector 18, Slum Rehabilitation Cluster', 'NGO/Receiver', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(10, 'EcoBio Sustainable Recyclers', '+91 98765 33001', 'recycler.ecobio@recycle.org', 'scrypt:32768:8:1$FLvHE8Hb95Z7ncus$140a504284646849eb66fdeca4796b2b5f9fe533b6e2a696da98de7b8247db1d9d9a2b6d6d8b383b76063b8b19205d36402ec889af4a2702c4e3fcfc9e0a93d0', 'Industrial Area Phase 2, Bio Park Road', 'Recycler', DATE_SUB(NOW(), INTERVAL 50 DAY)),
(11, 'GreenEarth Composting & Energy Hub', '+91 98765 33002', 'recycler.greenearth@compost.org', 'scrypt:32768:8:1$FLvHE8Hb95Z7ncus$140a504284646849eb66fdeca4796b2b5f9fe533b6e2a696da98de7b8247db1d9d9a2b6d6d8b383b76063b8b19205d36402ec889af4a2702c4e3fcfc9e0a93d0', 'Agri-Tech Zone, Outer Bypass Highway', 'Recycler', DATE_SUB(NOW(), INTERVAL 42 DAY));

-- ----------------------------------------------------------------------------
-- 2. Insert NGO_RECEIVER Profiles
-- ----------------------------------------------------------------------------
INSERT INTO `NGO_RECEIVER` (`NGO_ID`, `User_ID`, `Delivers_To_Center_ID`, `NGO_Name`, `Address`, `Contact_No`, `License_No`, `NGO_Type`, `Email`, `Website`) VALUES
(1, 7, 1, 'Hope Feeding Foundation', 'Building 24, Community Care Layout, East Hub', '+91 98765 22001', 'NGO-DL-2023-8891', 'Food Bank / NGO', 'ngo.hope@charity.org', 'https://hopefeeding.org'),
(2, 8, 2, 'Smiles Shelter & Care Home', 'Near Ashoka Pillar, Old Cantonment', '+91 98765 22002', 'NGO-KA-2021-4512', 'Homeless Shelter', 'ngo.smiles@shelter.org', 'https://smilesshelter.org'),
(3, 9, 3, 'Annapurna Hunger Relief Mission', 'Sector 18, Slum Rehabilitation Cluster', '+91 98765 22003', 'NGO-MH-2022-7729', 'Charity / Kitchen', 'ngo.annapurna@relief.org', 'https://annapurnarelieftrust.org');

-- ----------------------------------------------------------------------------
-- 3. Insert COLLECTION_CENTER Hubs (Pune Municipal & Metro Locations)
-- ----------------------------------------------------------------------------
INSERT INTO `COLLECTION_CENTER` (`Center_ID`, `Center_Name`, `Address`, `Contact_No`, `Capacity`, `Current_Occupancy`, `Center_Type`, `Latitude`, `Longitude`) VALUES
(1, 'Shivajinagar Central Food & Cold Storage Hub', 'Shivajinagar Bus Station Complex, JM Road, Pune - 411005', '+91 20 2553 9101', 3500.00, 850.00, 'Central Hub', 18.531400, 73.844600),
(2, 'Hadapsar Mega Composting & Organic Processing Depot', 'Plot 14, Hadapsar Industrial Estate Phase 1, Near Gadital, Pune - 411028', '+91 20 2687 4402', 2500.00, 620.00, 'Composting Unit', 18.508900, 73.925900),
(3, 'Khadakwasla Agro-Biogas & Renewable Energy Plant', 'Khadakwasla Dam Link Road, Near Sinhagad Foothills, Pune - 411024', '+91 20 2439 8803', 3000.00, 480.00, 'Biogas Plant', 18.441800, 73.763400),
(4, 'Kothrud Clean Material & Packaging Recycling Center', 'Paud Road, Near Vanaz Metro Station, Kothrud, Pune - 411038', '+91 20 2544 3304', 1800.00, 310.00, 'Recycling Depot', 18.507400, 73.807700),
(5, 'Hinjawadi Infotech Bio-Triage & Cold Storage Facility', 'Phase 1, Hinjawadi Rajiv Gandhi Infotech Park, Pune - 411057', '+91 20 6652 1105', 2200.00, 240.00, 'Central Hub', 18.591300, 73.738900),
(6, 'Viman Nagar Community Redistribution & Composting Hub', 'New Airport Road, Near Symbiosis Campus, Viman Nagar, Pune - 411014', '+91 20 2663 7706', 2000.00, 350.00, 'Composting Unit', 18.567900, 73.914300);

-- ----------------------------------------------------------------------------
-- 4. Insert DONATIONS
-- Demonstrates Available, Claimed, Scheduled, Completed, and Expired states
-- ----------------------------------------------------------------------------
INSERT INTO `DONATION` (`Donation_ID`, `User_ID`, `Claimed_By_NGO_ID`, `Food_Type`, `Quantity`, `Unit`, `Packaging_Type`, `Pickup_Address`, `Food_Category`, `Prepared_On`, `Expiry_Date`, `Status`, `Donation_Time`) VALUES
-- Active Available Donations (Ready for NGOs to claim)
(1, 2, NULL, 'Cooked Vegetable Biryani & Raita', 45.00, 'kg', 'Sealed Food-Grade Containers', 'Shop 12-14, Food Street, Indiranagar', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_ADD(NOW(), INTERVAL 14 HOUR), 'Available', DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, 4, NULL, 'Fresh Artisan Sourdough & Multigrain Loaves', 35.00, 'kg', 'Individual Paper Bags in Crates', '88 Mall Road, Central Market', 'Bakery', DATE_SUB(NOW(), INTERVAL 6 HOUR), DATE_ADD(NOW(), INTERVAL 36 HOUR), 'Available', DATE_SUB(NOW(), INTERVAL 5 HOUR)),
(3, 5, NULL, 'Fresh Farm Apples, Oranges & Pears', 80.00, 'kg', 'Ventilated Wooden Crates', 'Plot 45, APMC Mandi Complex, South Zone', 'Fruits & Vegetables', DATE_SUB(NOW(), INTERVAL 12 HOUR), DATE_ADD(NOW(), INTERVAL 72 HOUR), 'Available', DATE_SUB(NOW(), INTERVAL 8 HOUR)),
(4, 3, NULL, 'Paneer Butter Masala with Jeera Rice', 60.00, 'kg', 'Insulated Stainless Steel Casks', 'Sector 4, Ring Road Expressway', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_ADD(NOW(), INTERVAL 10 HOUR), 'Available', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(5, 5, NULL, 'Unopened Canned Soups & Beans', 120.00, 'kg', 'Original Sealed Carton Boxes', 'Plot 45, APMC Mandi Complex, South Zone', 'Packaged/Canned', DATE_SUB(NOW(), INTERVAL 5 DAY), DATE_ADD(NOW(), INTERVAL 60 DAY), 'Available', DATE_SUB(NOW(), INTERVAL 1 DAY)),

-- Scheduled & In-Transit Donations
(6, 6, 1, 'College Mess Steamed Rice & Dal Makhani', 55.00, 'kg', 'Sealed Thermal Food Dispensers', 'Campus Block C, University Enclave', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 4 HOUR), DATE_ADD(NOW(), INTERVAL 8 HOUR), 'Scheduled', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(7, 2, 2, 'Assorted Vegetable Sandwiches & Rolls', 25.00, 'kg', 'Clamshell Biodegradable Trays', 'Shop 12-14, Food Street, Indiranagar', 'Bakery', DATE_SUB(NOW(), INTERVAL 5 HOUR), DATE_ADD(NOW(), INTERVAL 7 HOUR), 'Scheduled', DATE_SUB(NOW(), INTERVAL 4 HOUR)),

-- Completed Donations (With Pickups & Reviews)
(8, 2, 1, 'Wedding Banquet Pulao, Paneer & Roti', 110.00, 'kg', 'Insulated Thermal Boxes', 'Indiranagar Banquet Hall', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 6 DAY), DATE_SUB(NOW(), INTERVAL 5 DAY), 'Completed', DATE_SUB(NOW(), INTERVAL 6 DAY)),
(9, 3, 2, 'Luxury Buffet Assorted Cooked Meals', 95.00, 'kg', 'Sealed Food Containers', 'Sector 4, Ring Road Expressway', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY), 'Completed', DATE_SUB(NOW(), INTERVAL 12 DAY)),
(10, 4, 3, 'Whole Wheat Dinner Breads & Buns', 40.00, 'kg', 'Packaged Carton Boxes', '88 Mall Road, Central Market', 'Bakery', DATE_SUB(NOW(), INTERVAL 15 DAY), DATE_SUB(NOW(), INTERVAL 14 DAY), 'Completed', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(11, 5, 1, 'Surplus Farm Fresh Spinach, Carrots & Cabbage', 150.00, 'kg', 'Mesh Crates', 'Plot 45, APMC Mandi Complex, South Zone', 'Fruits & Vegetables', DATE_SUB(NOW(), INTERVAL 18 DAY), DATE_SUB(NOW(), INTERVAL 16 DAY), 'Completed', DATE_SUB(NOW(), INTERVAL 18 DAY)),

-- Expired/Cancelled Donation (Used for viva demonstration of status transitions)
(12, 6, NULL, 'Mess Breakfast Idli & Sambar (Spoiled)', 30.00, 'kg', 'Open Trays', 'Campus Block C, University Enclave', 'Cooked Food', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), 'Expired', DATE_SUB(NOW(), INTERVAL 3 DAY));

-- ----------------------------------------------------------------------------
-- 5. Insert PICKUPS
-- ----------------------------------------------------------------------------
INSERT INTO `PICKUP` (`Pickup_ID`, `Donation_ID`, `Center_ID`, `Pickup_Time`, `Vehicle_No`, `Driver_Name`, `Notes`, `Status`, `Completed_At`) VALUES
(1, 6, 1, DATE_ADD(NOW(), INTERVAL 2 HOUR), 'DL-01-AX-9921', 'Ramesh Kumar', 'Call mess supervisor upon arrival at Gate 2', 'Scheduled', NULL),
(2, 7, 2, DATE_ADD(NOW(), INTERVAL 1 HOUR), 'KA-04-MB-4412', 'Sunil Jadhav', 'Fragile sandwiches, transport in upright chill box', 'Scheduled', NULL),
(3, 8, 1, DATE_SUB(NOW(), INTERVAL 6 DAY), 'DL-01-AX-9921', 'Ramesh Kumar', 'Late night emergency pickup completed on schedule', 'Completed', DATE_SUB(NOW(), INTERVAL 6 DAY)),
(4, 9, 3, DATE_SUB(NOW(), INTERVAL 12 DAY), 'MH-12-PQ-8833', 'Amit Deshmukh', 'Direct delivery to Smiles Shelter kitchen done', 'Completed', DATE_SUB(NOW(), INTERVAL 12 DAY)),
(5, 10, 2, DATE_SUB(NOW(), INTERVAL 15 DAY), 'KA-04-MB-4412', 'Sunil Jadhav', 'Bread received fresh, distributed to slum shelter', 'Completed', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(6, 11, 1, DATE_SUB(NOW(), INTERVAL 18 DAY), 'DL-01-AX-9921', 'Ramesh Kumar', 'Bulk vegetable consignment handled successfully', 'Completed', DATE_SUB(NOW(), INTERVAL 18 DAY));

-- ----------------------------------------------------------------------------
-- 6. Insert REPORTS
-- ----------------------------------------------------------------------------
INSERT INTO `REPORT` (`Report_ID`, `Center_ID`, `Generated_By_User_ID`, `Report_Type`, `Start_Date`, `End_Date`, `Generated_On`, `Summary`) VALUES
(1, 1, 1, 'Monthly Summary', DATE_SUB(CURDATE(), INTERVAL 30 DAY), CURDATE(), DATE_SUB(NOW(), INTERVAL 2 DAY), 'Central Hub managed 45 successful food distributions, rescuing 1,420 kg of edible meals with 98.2% on-time pickup dispatch.'),
(2, 2, 10, 'Waste Processing', DATE_SUB(CURDATE(), INTERVAL 15 DAY), CURDATE(), DATE_SUB(NOW(), INTERVAL 5 DAY), 'North Organic Depot processed 620 kg of kitchen scraps yielding 186 kg of premium organic fertilizer vermicompost.'),
(3, 3, 11, 'Daily Log', DATE_SUB(CURDATE(), INTERVAL 1 DAY), CURDATE(), DATE_SUB(NOW(), INTERVAL 1 DAY), 'Anaerobic digester batch charged with 480 kg spoiling vegetable waste, generating 72 m3 of methane-rich biogas.'),
(4, 4, 10, 'Annual Impact', DATE_SUB(CURDATE(), INTERVAL 365 DAY), CURDATE(), DATE_SUB(NOW(), INTERVAL 10 DAY), 'Annual audit revealed diversion of 24.5 tons of organic waste from municipal landfills, sequestering approx 18.2 tons CO2e.'),
(5, 1, 1, 'Donation Audit', DATE_SUB(CURDATE(), INTERVAL 60 DAY), CURDATE(), DATE_SUB(NOW(), INTERVAL 15 DAY), 'Verified zero health incidents across 150+ donations delivered to partner food banks.');

-- ----------------------------------------------------------------------------
-- 7. Insert WASTE_ITEMS
-- Inedible waste received at processing centers
-- ----------------------------------------------------------------------------
INSERT INTO `WASTE_ITEM` (`Waste_ID`, `Center_ID`, `Report_ID`, `Waste_Type`, `Quantity`, `Unit`, `Description`, `Recorded_Date`, `Status`) VALUES
(1, 2, 2, 'Expired Food Scraps', 220.00, 'kg', 'Sour dairy and discarded bakery trimmings from local catering', DATE_SUB(NOW(), INTERVAL 8 DAY), 'Processed'),
(2, 2, 2, 'Organic Kitchen Waste', 400.00, 'kg', 'Raw potato skins, cabbage leaves, and onion trimmings from food hub', DATE_SUB(NOW(), INTERVAL 7 DAY), 'Processed'),
(3, 3, 3, 'Spoiled Produce', 480.00, 'kg', 'Overripe papayas, tomatoes, and bruised apples rejected at market', DATE_SUB(NOW(), INTERVAL 3 DAY), 'In Processing'),
(4, 1, 1, 'Packaging / Inorganics', 150.00, 'kg', 'Corrugated cardboard boxes, LDPE covers, and packing straps', DATE_SUB(NOW(), INTERVAL 4 DAY), 'Pending'),
(5, 4, 4, 'Biomass Residue', 310.00, 'kg', 'Dry corn husks, straw packing, and spent grain mash', DATE_SUB(NOW(), INTERVAL 2 DAY), 'Pending'),
(6, 2, NULL, 'Organic Kitchen Waste', 280.00, 'kg', 'Freshly received restaurant peelings and waste mash', DATE_SUB(NOW(), INTERVAL 12 HOUR), 'Pending'),
(7, 3, NULL, 'Spoiled Produce', 190.00, 'kg', 'Fermenting vegetable scraps collected from college mess', DATE_SUB(NOW(), INTERVAL 6 HOUR), 'Pending'),
(8, 1, NULL, 'Packaging / Inorganics', 95.00, 'kg', 'Recyclable aluminum food tins and tin foil wrap', DATE_SUB(NOW(), INTERVAL 4 HOUR), 'Pending');

-- ----------------------------------------------------------------------------
-- 8. Insert PROCESS Records
-- Biological / material conversion runs
-- ----------------------------------------------------------------------------
INSERT INTO `PROCESS` (`Process_ID`, `Center_ID`, `Waste_ID`, `Process_Type`, `Start_Date`, `End_Date`, `Input_Quantity`, `Output_Quantity`, `Remarks`, `Status`) VALUES
(1, 2, 1, 'Composting', DATE_SUB(NOW(), INTERVAL 8 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY), 220.00, 75.00, 'Aerobic windrow composting completed. Yielded rich compost.', 'Completed'),
(2, 2, 2, 'Composting', DATE_SUB(NOW(), INTERVAL 7 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY), 400.00, 140.00, 'Thermophilic composting cycle finished at 60C, free of pathogens.', 'Completed'),
(3, 3, 3, 'Biogas', DATE_SUB(NOW(), INTERVAL 3 DAY), NULL, 480.00, 0.00, 'Active anaerobic digestion stage 2 in 500L CSTR tank. Methane purity 64%.', 'In Progress'),
(4, 4, 4, 'Recycling', DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 9 DAY), 200.00, 185.00, 'Hydropulping and cardboard baling delivered to packaging mill.', 'Completed'),
(5, 3, NULL, 'Biogas', DATE_SUB(NOW(), INTERVAL 20 DAY), DATE_SUB(NOW(), INTERVAL 16 DAY), 550.00, 88.00, 'Successful biogas generation run: 88 m3 clean methane produced for heating.', 'Completed'),
(6, 4, NULL, 'Recycling', DATE_SUB(NOW(), INTERVAL 25 DAY), DATE_SUB(NOW(), INTERVAL 24 DAY), 320.00, 290.00, 'Crushed aluminum container scrap melted and remolded into raw ingots.', 'Completed');

-- ----------------------------------------------------------------------------
-- 9. Insert REVIEWS
-- Feedback from NGOs and recipients for completed donations
-- ----------------------------------------------------------------------------
INSERT INTO `REVIEW` (`Review_ID`, `Donation_ID`, `User_ID`, `Rating`, `Comment`, `Review_Date`) VALUES
(1, 8, 7, 5, 'Exceptional quality food! The biryani was piping hot and neatly sealed in sterile containers. We fed 220 shelter residents with dignity.', DATE_SUB(NOW(), INTERVAL 5 DAY)),
(2, 9, 8, 5, 'Hyatt Regency hospitality team packaged the surplus flawlessly. Fresh, delicious, and nutritious meals received with full safety certs.', DATE_SUB(NOW(), INTERVAL 11 DAY)),
(3, 10, 9, 4, 'Breads and rolls were soft and freshly baked. Saved our community kitchen considerable budget for this morning breakfast.', DATE_SUB(NOW(), INTERVAL 14 DAY)),
(4, 11, 7, 5, 'Superb consignment of fresh farm vegetables! Zero rot, perfectly graded vegetables that helped cook hot meals for 3 straight days.', DATE_SUB(NOW(), INTERVAL 16 DAY));

SET FOREIGN_KEY_CHECKS = 1;

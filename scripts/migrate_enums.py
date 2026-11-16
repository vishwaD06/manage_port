import sys
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from db import get_db_connection

def migrate():
    conn = get_db_connection()
    cursor = conn.cursor()
    alters = [
        """ALTER TABLE donation MODIFY COLUMN Food_Category ENUM(
            'Cooked Food', 'Raw Groceries', 'Bakery', 'Fruits & Vegetables',
            'Packaged/Canned', 'Veg', 'Non-Veg', 'Vegetarian', 'Non-Vegetarian',
            'Cooked Food (Veg)', 'Cooked Food (Non-Veg)'
        ) NOT NULL COMMENT 'Categorization matching ER Diagram (Veg/Non-Veg)';""",

        """ALTER TABLE report MODIFY COLUMN Report_Type ENUM(
            'Daily', 'Monthly', 'Yearly', 'Daily Log', 'Monthly Summary',
            'Donation Audit', 'Waste Processing', 'Annual Impact'
        ) NOT NULL COMMENT 'Matches ER Diagram (Daily/Monthly/Yearly)';""",

        """ALTER TABLE waste_item MODIFY COLUMN Waste_Type ENUM(
            'Food', 'Organic', 'Inorganic', 'Expired Food Scraps', 'Organic Kitchen Waste',
            'Spoiled Produce', 'Packaging / Inorganics', 'Biomass Residue'
        ) NOT NULL COMMENT 'Matches ER Diagram (Food/Organic/Inorganic)';""",

        """ALTER TABLE process MODIFY COLUMN Process_Type ENUM(
            'Composting', 'Recycler', 'Recycling', 'Biogas'
        ) NOT NULL COMMENT 'Matches ER Diagram (Composting/Recycler/Biogas)';"""
    ]
    for sql in alters:
        try:
            cursor.execute(sql)
            print("Successfully executed ALTER")
        except Exception as e:
            print(f"Error: {e}")
    conn.commit()
    conn.close()
    print("All ENUM migrations completed successfully.")

if __name__ == "__main__":
    migrate()

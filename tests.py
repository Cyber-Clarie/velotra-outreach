import sqlite3
import unittest
from services.import_service import parse_import_data, analyze_import, commit_import

class TestPhase1(unittest.TestCase):
    def setUp(self):
        # Create an in-memory DB with the exact schema
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("""
            CREATE TABLE creators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                username TEXT NOT NULL UNIQUE,
                profile_url TEXT,
                niche TEXT,
                status TEXT DEFAULT 'NEW',
                date_added TEXT,
                last_contact_at TEXT,
                last_reply_at TEXT,
                next_action_at TEXT,
                followup_count INTEGER DEFAULT 0,
                notes TEXT,
                source TEXT DEFAULT 'MANUAL',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                scheduled_at TEXT,
                status TEXT DEFAULT 'PENDING',
                priority INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY(creator_id) REFERENCES creators(id)
            )
        """)
        
        # Insert a pre-existing creator (like the "test" creator)
        self.cursor.execute("""
            INSERT INTO creators (name, username, status, date_added)
            VALUES ('test user', 'existing_test', 'NEW', '2026-09-20')
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_import_workflow(self):
        csv_data = """username,name,niche,status,last_contact_at
new1,New User 1,Tech,,
new2,New User 2,Fashion,,
new3,New User 3,Food,,
existing_test,Test User,Gaming,NEW,
duplicate_in_csv,Dup 1,Tech,,
duplicate_in_csv,Dup 2,Tech,,
old_reactivation,Old User,Fitness,NO_RESPONSE,2026-08-01
"""
        # Parse
        parsed = parse_import_data(csv_data)
        self.assertEqual(len(parsed), 7)
        
        # Analyze (Preview)
        preview = analyze_import(parsed, self.conn)
        
        # We expect:
        # 3 new (new1, new2, new3)
        # 1 old (old_reactivation)
        # 2 duplicates (1 is 'existing_test' because it's in DB, 1 is the 2nd 'duplicate_in_csv')
        # Wait, 'duplicate_in_csv' is a new user but appears twice. 
        # The first occurrence goes to 'to_insert_new', the second goes to 'duplicates'.
        
        self.assertEqual(len(preview['to_insert_new']), 4) # new1, new2, new3, duplicate_in_csv (first instance)
        self.assertEqual(len(preview['to_insert_old']), 1) # old_reactivation
        
        # Duplicates skipped: 1 existing in db, 1 duplicate in csv
        self.assertEqual(len(preview['duplicates']), 2)
        
        # Commit
        success = commit_import(preview, self.conn)
        self.assertTrue(success)
        
        # Verify DB Actions
        self.cursor.execute("SELECT action_type, COUNT(*) as c FROM actions GROUP BY action_type")
        actions = {row['action_type']: row['c'] for row in self.cursor.fetchall()}
        
        # 4 INITIAL_DM actions, 1 REACTIVATION action
        self.assertEqual(actions.get('INITIAL_DM', 0), 4)
        self.assertEqual(actions.get('REACTIVATION', 0), 1)

if __name__ == '__main__':
    unittest.main()

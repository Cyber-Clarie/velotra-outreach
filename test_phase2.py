import sqlite3
import unittest
import datetime
from services.followup_service import get_due_actions, complete_action, handle_do_not_contact
import config

class TestPhase2(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        self.cursor.execute("""
            CREATE TABLE creators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                username TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'NEW',
                followup_count INTEGER DEFAULT 0
            )
        """)
        self.cursor.execute("""
            CREATE TABLE actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                scheduled_at TEXT,
                status TEXT DEFAULT 'PENDING',
                completed_at TEXT,
                FOREIGN KEY(creator_id) REFERENCES creators(id)
            )
        """)
        
        # Insert test creators
        for i in range(1, 6):
            self.cursor.execute("INSERT INTO creators (id, name, username) VALUES (?, ?, ?)", (i, f'user{i}', f'testuser{i}'))
            
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        
    def _create_action(self, creator_id, action_type, dt_str):
        self.cursor.execute("""
            INSERT INTO actions (creator_id, action_type, scheduled_at, status)
            VALUES (?, ?, ?, 'PENDING')
        """, (creator_id, action_type, dt_str))
        self.conn.commit()
        return self.cursor.lastrowid

    def test_queue_categories(self):
        now = datetime.datetime.now()
        
        # 1. Overdue action (past)
        overdue_dt = (now - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        self._create_action(1, 'INITIAL_DM', overdue_dt)
        
        # 2. Due now action
        duenow_dt = (now + datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        self._create_action(2, 'INITIAL_DM', duenow_dt)
        
        # 3. Upcoming action
        upcoming_dt = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        self._create_action(3, 'INITIAL_DM', upcoming_dt)
        
        due = get_due_actions(self.conn)
        
        self.assertEqual(len(due['OVERDUE']), 1)
        self.assertEqual(due['OVERDUE'][0]['creator_id'], 1)
        
        self.assertEqual(len(due['DUE_NOW']), 1)
        self.assertEqual(due['DUE_NOW'][0]['creator_id'], 2)
        
        self.assertEqual(len(due['UPCOMING']), 1)
        self.assertEqual(due['UPCOMING'][0]['creator_id'], 3)

    def test_laptop_off_catchup(self):
        # Action scheduled for yesterday
        past_dt = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        self._create_action(4, 'FOLLOW_UP', past_dt)
        
        due = get_due_actions(self.conn)
        self.assertEqual(len(due['OVERDUE']), 1)
        self.assertEqual(due['OVERDUE'][0]['scheduled_at'], past_dt)

    def test_completing_initial_dm_schedules_next(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_id = self._create_action(5, 'INITIAL_DM', now)
        
        success = complete_action(action_id, self.conn)
        self.assertTrue(success)
        
        # Check that it's completed
        self.cursor.execute("SELECT status FROM actions WHERE id = ?", (action_id,))
        self.assertEqual(self.cursor.fetchone()['status'], 'COMPLETED')
        
        # Check that creator is now CONTACTED
        self.cursor.execute("SELECT status, followup_count FROM creators WHERE id = 5")
        creator = self.cursor.fetchone()
        self.assertEqual(creator['status'], 'CONTACTED')
        self.assertEqual(creator['followup_count'], 1)
        
        # Check that new FOLLOW_UP is scheduled
        self.cursor.execute("SELECT * FROM actions WHERE creator_id = 5 AND status = 'PENDING'")
        new_action = self.cursor.fetchone()
        self.assertIsNotNone(new_action)
        self.assertEqual(new_action['action_type'], 'FOLLOW_UP')
        
        # It should be scheduled in the future (UPCOMING)
        due = get_due_actions(self.conn)
        self.assertEqual(len(due['UPCOMING']), 1)

    def test_max_followups(self):
        # Manually set followup_count to max
        self.cursor.execute("UPDATE creators SET followup_count = ? WHERE id = 1", (len(config.FOLLOW_UP_SCHEDULE),))
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        action_id = self._create_action(1, 'FOLLOW_UP', now)
        
        complete_action(action_id, self.conn)
        
        # Check that NO new action is scheduled
        self.cursor.execute("SELECT COUNT(*) as c FROM actions WHERE creator_id = 1 AND status = 'PENDING'")
        self.assertEqual(self.cursor.fetchone()['c'], 0)

    def test_do_not_contact(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._create_action(2, 'INITIAL_DM', now)
        self._create_action(2, 'FOLLOW_UP', now) # duplicate pending just to test
        
        success = handle_do_not_contact(2, self.conn)
        self.assertTrue(success)
        
        # Check creator status
        self.cursor.execute("SELECT status FROM creators WHERE id = 2")
        self.assertEqual(self.cursor.fetchone()['status'], 'DO_NOT_CONTACT')
        
        # Check pending actions are cancelled
        self.cursor.execute("SELECT status FROM actions WHERE creator_id = 2")
        rows = self.cursor.fetchall()
        for r in rows:
            self.assertEqual(r['status'], 'CANCELLED')

if __name__ == '__main__':
    unittest.main()

import os
import unittest
import database

class TestDatabaseOperations(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Override database path to use a separate test database
        cls.orig_db_path = database.DB_PATH
        database.DB_PATH = "test_vbcua.db"
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        # Restore original path and clean up test database file
        database.DB_PATH = cls.orig_db_path
        if os.path.exists("test_vbcua.db"):
            try:
                os.remove("test_vbcua.db")
            except OSError:
                pass

    def test_user_authentication_flow(self):
        # Register a user
        user_id = database.register_user("Test Alice", "alice@test.com", "my_secure_pwd", "Student")
        self.assertIsNotNone(user_id)
        
        # Verify duplicate registration returns None
        dup_id = database.register_user("Dup Alice", "alice@test.com", "other_pwd", "Student")
        self.assertIsNone(dup_id)
        
        # Authenticate with correct password
        user = database.authenticate_user("alice@test.com", "my_secure_pwd")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Test Alice")
        self.assertEqual(user["role"], "Student")
        
        # Authenticate with incorrect password
        bad_user = database.authenticate_user("alice@test.com", "wrong_pwd")
        self.assertIsNone(bad_user)
        
        # Retrieve by id
        retrieved_user = database.get_user(user_id)
        self.assertEqual(retrieved_user["email"], "alice@test.com")

    def test_sessions(self):
        user_id = database.register_user("Session Bob", "bob@test.com", "pwd", "Educator")
        self.assertIsNotNone(user_id)
        
        # Start session
        session_id = database.start_session(user_id)
        self.assertIsNotNone(session_id)
        
        # Get active session
        active = database.get_active_session(user_id)
        self.assertEqual(active["session_id"], session_id)
        self.assertEqual(active["status"], "ACTIVE")
        
        # End session
        database.end_session(session_id)
        active_after = database.get_active_session(user_id)
        self.assertIsNone(active_after)

    def test_concepts_crud(self):
        user_id = database.register_user("Concept User", "concept@test.com", "pwd", "Student")
        self.assertIsNotNone(user_id)
        
        # Create concept
        ref_id = database.add_reference_concept(user_id, "AI Test Concept", "This is some reference text.")
        self.assertIsNotNone(ref_id)
        
        # Retrieve by id
        concept = database.get_reference_concept(ref_id)
        self.assertEqual(concept["concept_title"], "AI Test Concept")
        
        # Retrieve user-specific concepts list
        user_concepts = database.get_user_reference_concepts(user_id)
        self.assertEqual(len(user_concepts), 1)
        self.assertEqual(user_concepts[0]["concept_title"], "AI Test Concept")
        
        # Delete concept
        success = database.delete_reference_concept(ref_id)
        self.assertTrue(success)
        
        # Retrieve after deletion
        deleted_concept = database.get_reference_concept(ref_id)
        self.assertIsNone(deleted_concept)

    def test_evaluation_saving_and_detail_reload(self):
        user_id = database.register_user("User Charlie", "charlie@test.com", "pwd", "Student")
        ref_id = database.add_reference_concept(user_id, "Database Systems", "DBMS explanation text")
        
        # Save evaluation
        result_id = database.save_evaluation(
            user_id=user_id,
            ref_concept_id=ref_id,
            file_name="test_speech.wav",
            file_path="uploads/test_speech.wav",
            duration_sec=10.0,
            transcript_text="Databases store information in structured formats.",
            filler_word_count=2,
            total_words=8,
            filler_ratio=0.25,
            similarity_score=0.75,
            pause_ratio=0.15,
            rms_energy=0.08,
            zero_crossing_rate=0.04,
            overall_score=80.0,
            understanding_level="Strong Understanding",
            notes="JUnit Unit Test"
        )
        
        self.assertIsNotNone(result_id)
        
        # Save report
        report_id = database.save_report(result_id, "reports/test_report.pdf", 45)
        self.assertIsNotNone(report_id)
        
        # Retrieve history
        history = database.get_user_evaluation_history(user_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["concept_title"], "Database Systems")
        self.assertEqual(history[0]["overall_score"], 80.0)
        
        # Retrieve detailed view
        detail = database.get_evaluation_detail(result_id)
        self.assertEqual(detail["file_name"], "test_speech.wav")
        self.assertEqual(detail["transcript_text"], "Databases store information in structured formats.")
        self.assertEqual(detail["understanding_level"], "Strong Understanding")
        self.assertEqual(detail["pdf_path"], "reports/test_report.pdf")
        self.assertEqual(detail["file_size_kb"], 45)

if __name__ == '__main__':
    unittest.main()

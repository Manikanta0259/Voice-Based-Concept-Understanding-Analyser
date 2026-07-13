import sqlite3
import os
import hashlib
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "vbcua.db")

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA256 and a random salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password against its stored hash."""
    try:
        salt_hex, hash_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash == expected_hash
    except Exception:
        return False

def get_db_connection():
    """Returns a connection to the SQLite database with Foreign Keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes all database tables from the VBCUA ER Diagram, migrating if necessary."""
    # Check if users table needs migration (V1 to V2 schema change)
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        needs_migration = False
        try:
            cursor.execute("SELECT password_hash FROM users LIMIT 1")
        except sqlite3.OperationalError:
            needs_migration = True
        conn.close()
        
        if needs_migration:
            # Recreate all tables in order of dependency to clear the schema
            conn = sqlite3.connect(DB_PATH)
            conn.execute("PRAGMA foreign_keys = OFF;")
            tables = ["reports", "evaluation_results", "audio_features", "semantic_similarities", 
                      "filler_word_stats", "transcripts", "audio_files", "reference_concepts", 
                      "sessions", "users"]
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
            conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. users table (V2: Added password_hash)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role VARCHAR(20) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        ended_at DATETIME,
        status VARCHAR(20) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    
    # 3. reference_concepts table (V2: Added user_id FK, UNIQUE(user_id, concept_title))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reference_concepts (
        ref_concept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        concept_title VARCHAR(255) NOT NULL,
        concept_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        UNIQUE (user_id, concept_title)
    );
    """)
    
    # 4. audio_files table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audio_files (
        audio_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_name VARCHAR(255) NOT NULL,
        file_path VARCHAR(255) NOT NULL,
        duration_sec FLOAT NOT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(20) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)
    
    # 5. transcripts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
        audio_id INTEGER UNIQUE NOT NULL,
        transcript_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (audio_id) REFERENCES audio_files(audio_id) ON DELETE CASCADE
    );
    """)
    
    # 6. filler_word_stats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS filler_word_stats (
        filler_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcript_id INTEGER UNIQUE NOT NULL,
        filler_word_count INTEGER NOT NULL,
        total_words INTEGER NOT NULL,
        filler_ratio FLOAT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transcript_id) REFERENCES transcripts(transcript_id) ON DELETE CASCADE
    );
    """)
    
    # 7. semantic_similarities table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semantic_similarities (
        similarity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transcript_id INTEGER NOT NULL,
        ref_concept_id INTEGER NOT NULL,
        similarity_score FLOAT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transcript_id) REFERENCES transcripts(transcript_id) ON DELETE CASCADE,
        FOREIGN KEY (ref_concept_id) REFERENCES reference_concepts(ref_concept_id) ON DELETE CASCADE
    );
    """)
    
    # 8. audio_features table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audio_features (
        feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
        audio_id INTEGER UNIQUE NOT NULL,
        pause_ratio FLOAT NOT NULL,
        rms_energy FLOAT NOT NULL,
        zero_crossing_rate FLOAT NOT NULL,
        duration_sec FLOAT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (audio_id) REFERENCES audio_files(audio_id) ON DELETE CASCADE
    );
    """)
    
    # 9. evaluation_results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evaluation_results (
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        audio_id INTEGER NOT NULL,
        ref_concept_id INTEGER NOT NULL,
        overall_score FLOAT NOT NULL,
        understanding_level VARCHAR(20) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (audio_id) REFERENCES audio_files(audio_id) ON DELETE CASCADE,
        FOREIGN KEY (ref_concept_id) REFERENCES reference_concepts(ref_concept_id) ON DELETE CASCADE
    );
    """)
    
    # 10. reports table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id INTEGER UNIQUE NOT NULL,
        pdf_path VARCHAR(255) NOT NULL,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        file_size_kb INTEGER NOT NULL,
        FOREIGN KEY (result_id) REFERENCES evaluation_results(result_id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

# ----------------- User Registration & Auth -----------------

def register_user(name, email, password, role):
    """Registers a new user with secure hashed password. Returns user_id or None."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        pwd_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (name, email, pwd_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None  # Email already registered
    finally:
        conn.close()

def authenticate_user(email, password):
    """Authenticates user by email and password. Returns user dict or None."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if row and verify_password(password, row['password_hash']):
        return dict(row)
    return None

def get_user(user_id):
    """Retrieves a user by id."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ----------------- Session Operations -----------------

def start_session(user_id):
    """Starts a new session. Returns session_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (user_id, status) VALUES (?, ?)",
        (user_id, 'ACTIVE')
    )
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id

def end_session(session_id):
    """Ends a session."""
    conn = get_db_connection()
    conn.execute(
        "UPDATE sessions SET ended_at = ?, status = ? WHERE session_id = ?",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'COMPLETED', session_id)
    )
    conn.commit()
    conn.close()

def get_active_session(user_id):
    """Retrieves active session."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM sessions WHERE user_id = ? AND status = 'ACTIVE' ORDER BY started_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

# ----------------- User-Specific Reference Concepts CRUD -----------------

def add_reference_concept(user_id, title, text):
    """Adds a new custom reference concept for a specific user. Returns ref_concept_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reference_concepts (user_id, concept_title, concept_text) VALUES (?, ?, ?)",
            (user_id, title, text)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ref_concept_id FROM reference_concepts WHERE user_id = ? AND concept_title = ?",
            (user_id, title)
        )
        row = cursor.fetchone()
        return row['ref_concept_id'] if row else None
    finally:
        conn.close()

def delete_reference_concept(ref_concept_id):
    """Deletes a custom concept by id. Cascade deletes evaluate results and reports."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reference_concepts WHERE ref_concept_id = ?", (ref_concept_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_reference_concept(ref_concept_id):
    """Retrieves concept by id."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM reference_concepts WHERE ref_concept_id = ?", (ref_concept_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_reference_concepts(user_id):
    """Retrieves all custom reference concepts created by a specific user."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM reference_concepts WHERE user_id = ? ORDER BY concept_title",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ----------------- Evaluation Persistence Transaction -----------------

def save_evaluation(
    user_id,
    ref_concept_id,
    file_name,
    file_path,
    duration_sec,
    transcript_text,
    filler_word_count,
    total_words,
    filler_ratio,
    similarity_score,
    pause_ratio,
    rms_energy,
    zero_crossing_rate,
    overall_score,
    understanding_level,
    notes=None
):
    """Saves entire evaluation pipeline in a transaction."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Insert into audio_files
        cursor.execute(
            "INSERT INTO audio_files (user_id, file_name, file_path, duration_sec, status) VALUES (?, ?, ?, ?, ?)",
            (user_id, file_name, file_path, duration_sec, 'PROCESSED')
        )
        audio_id = cursor.lastrowid
        
        # 2. Insert into transcripts
        cursor.execute(
            "INSERT INTO transcripts (audio_id, transcript_text) VALUES (?, ?)",
            (audio_id, transcript_text)
        )
        transcript_id = cursor.lastrowid
        
        # 3. Insert into filler_word_stats
        cursor.execute(
            "INSERT INTO filler_word_stats (transcript_id, filler_word_count, total_words, filler_ratio) VALUES (?, ?, ?, ?)",
            (transcript_id, filler_word_count, total_words, filler_ratio)
        )
        
        # 4. Insert into semantic_similarities
        cursor.execute(
            "INSERT INTO semantic_similarities (transcript_id, ref_concept_id, similarity_score) VALUES (?, ?, ?)",
            (transcript_id, ref_concept_id, similarity_score)
        )
        
        # 5. Insert into audio_features
        cursor.execute(
            "INSERT INTO audio_features (audio_id, pause_ratio, rms_energy, zero_crossing_rate, duration_sec) VALUES (?, ?, ?, ?, ?)",
            (audio_id, pause_ratio, rms_energy, zero_crossing_rate, duration_sec)
        )
        
        # 6. Insert into evaluation_results
        cursor.execute(
            "INSERT INTO evaluation_results (audio_id, ref_concept_id, overall_score, understanding_level, notes) VALUES (?, ?, ?, ?, ?)",
            (audio_id, ref_concept_id, overall_score, understanding_level, notes)
        )
        result_id = cursor.lastrowid
        
        conn.commit()
        return result_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_report(result_id, pdf_path, file_size_kb):
    """Saves report details linked to an evaluation result."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (result_id, pdf_path, file_size_kb) VALUES (?, ?, ?)",
            (result_id, pdf_path, int(file_size_kb))
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reports SET pdf_path = ?, file_size_kb = ?, generated_at = CURRENT_TIMESTAMP WHERE result_id = ?",
            (pdf_path, int(file_size_kb), result_id)
        )
        conn.commit()
        return True
    finally:
        conn.close()

# ----------------- History & Details Retrieval -----------------

def get_user_evaluation_history(user_id):
    """Retrieves evaluations for a user, filtered and ordered."""
    conn = get_db_connection()
    query = """
    SELECT 
        er.result_id,
        er.overall_score,
        er.understanding_level,
        er.created_at,
        rc.concept_title,
        af.file_name,
        af.duration_sec
    FROM evaluation_results er
    JOIN audio_files af ON er.audio_id = af.audio_id
    JOIN reference_concepts rc ON er.ref_concept_id = rc.ref_concept_id
    WHERE af.user_id = ?
    ORDER BY er.created_at DESC
    """
    rows = conn.execute(query, (user_id,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_evaluation_detail(result_id):
    """Retrieves full evaluation metrics detailed structure."""
    conn = get_db_connection()
    query = """
    SELECT 
        er.result_id,
        er.overall_score,
        er.understanding_level,
        er.created_at as evaluated_at,
        er.notes,
        rc.ref_concept_id,
        rc.concept_title,
        rc.concept_text as reference_text,
        af.audio_id,
        af.file_name,
        af.file_path,
        af.duration_sec,
        t.transcript_text,
        fws.filler_word_count,
        fws.total_words,
        fws.filler_ratio,
        ss.similarity_score,
        au.pause_ratio,
        au.rms_energy,
        au.zero_crossing_rate,
        r.pdf_path,
        r.file_size_kb,
        r.generated_at as report_generated_at
    FROM evaluation_results er
    JOIN audio_files af ON er.audio_id = af.audio_id
    JOIN reference_concepts rc ON er.ref_concept_id = rc.ref_concept_id
    LEFT JOIN transcripts t ON af.audio_id = t.audio_id
    LEFT JOIN filler_word_stats fws ON t.transcript_id = fws.transcript_id
    LEFT JOIN semantic_similarities ss ON t.transcript_id = ss.transcript_id AND rc.ref_concept_id = ss.ref_concept_id
    LEFT JOIN audio_features au ON af.audio_id = au.audio_id
    LEFT JOIN reports r ON er.result_id = r.result_id
    WHERE er.result_id = ?
    """
    row = conn.execute(query, (result_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

import sqlite3
import os

DB_PATH = "research_tracker.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Queries table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        query_text TEXT NOT NULL,
        engine TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """)
    
    # Resources table (papers, links, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        authors TEXT,
        journal TEXT,
        year INTEGER,
        url TEXT,
        doi TEXT,
        abstract TEXT,
        source_query_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (source_query_id) REFERENCES queries(id) ON DELETE SET NULL
    )
    """)
    
    # Decisions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resource_id INTEGER UNIQUE NOT NULL,
        status TEXT NOT NULL, -- 'Selected', 'Rejected', 'Deferred'
        justification TEXT NOT NULL,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE
    )
    """)
    
    # Timeline events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        event_type TEXT NOT NULL, -- 'PROJECT_CREATED', 'QUERY_LOGGED', 'RESOURCE_ADDED', 'DECISION_MADE', 'SCOPE_CHANGED'
        description TEXT NOT NULL,
        ref_id INTEGER, -- e.g., query_id or resource_id
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# Project Helpers
def create_project(name, description):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO projects (name, description) VALUES (?, ?)", (name, description))
        project_id = cursor.lastrowid
        # Log to timeline
        cursor.execute("""
        INSERT INTO timeline_events (project_id, event_type, description, ref_id)
        VALUES (?, 'PROJECT_CREATED', ?, ?)
        """, (project_id, f"Project '{name}' was created.", project_id))
        conn.commit()
        return project_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_projects():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_project(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def delete_project(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

# Query Helpers
def log_query(project_id, query_text, engine, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO queries (project_id, query_text, engine, notes)
    VALUES (?, ?, ?, ?)
    """, (project_id, query_text, engine, notes))
    query_id = cursor.lastrowid
    # Log to timeline
    cursor.execute("""
    INSERT INTO timeline_events (project_id, event_type, description, ref_id)
    VALUES (?, 'QUERY_LOGGED', ?, ?)
    """, (project_id, f"Logged search query: '{query_text}' on {engine}.", query_id))
    conn.commit()
    conn.close()
    return query_id

def get_queries(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM queries WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Resource Helpers
def add_resource(project_id, title, authors, journal, year, url, doi, abstract, source_query_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO resources (project_id, title, authors, journal, year, url, doi, abstract, source_query_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, title, authors, journal, year, url, doi, abstract, source_query_id))
    resource_id = cursor.lastrowid
    # Log to timeline
    cursor.execute("""
    INSERT INTO timeline_events (project_id, event_type, description, ref_id)
    VALUES (?, 'RESOURCE_ADDED', ?, ?)
    """, (project_id, f"Added resource: '{title}'.", resource_id))
    conn.commit()
    conn.close()
    return resource_id

def get_resources(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.*, d.status, d.justification, d.notes as decision_notes, d.updated_at as decision_date
    FROM resources r
    LEFT JOIN decisions d ON r.id = d.resource_id
    WHERE r.project_id = ?
    ORDER BY r.created_at DESC
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# Decision Helpers
def record_decision(resource_id, status, justification, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get project_id and title
    cursor.execute("SELECT project_id, title FROM resources WHERE id = ?", (resource_id,))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return False
    project_id, title = res['project_id'], res['title']
    
    # Insert or replace decision
    cursor.execute("""
    INSERT INTO decisions (resource_id, status, justification, notes, updated_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(resource_id) DO UPDATE SET
        status=excluded.status,
        justification=excluded.justification,
        notes=excluded.notes,
        updated_at=CURRENT_TIMESTAMP
    """, (resource_id, status, justification, notes))
    
    # Log to timeline
    cursor.execute("""
    INSERT INTO timeline_events (project_id, event_type, description, ref_id)
    VALUES (?, 'DECISION_MADE', ?, ?)
    """, (project_id, f"Decided to mark '{title}' as {status}. Justification: {justification}", resource_id))
    
    conn.commit()
    conn.close()
    return True

# Timeline Helpers
def get_timeline(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM timeline_events WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def log_scope_change(project_id, change_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO timeline_events (project_id, event_type, description)
    VALUES (?, 'SCOPE_CHANGED', ?)
    """, (project_id, f"Project scope changed: {change_description}"))
    conn.commit()
    conn.close()

# Analytics
def get_analytics(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Resource decisions count
    cursor.execute("""
    SELECT d.status, COUNT(d.id) as count
    FROM decisions d
    JOIN resources r ON d.resource_id = r.id
    WHERE r.project_id = ?
    GROUP BY d.status
    """, (project_id,))
    decisions = cursor.fetchall()
    
    # Unevaluated resources count
    cursor.execute("""
    SELECT COUNT(r.id) as count
    FROM resources r
    LEFT JOIN decisions d ON r.id = d.resource_id
    WHERE r.project_id = ? AND d.id IS NULL
    """, (project_id,))
    unevaluated = cursor.fetchone()['count']
    
    # Total queries
    cursor.execute("SELECT COUNT(id) as count FROM queries WHERE project_id = ?", (project_id,))
    queries_count = cursor.fetchone()['count']
    
    conn.close()
    return {
        "decisions": {d['status']: d['count'] for d in decisions},
        "unevaluated": unevaluated,
        "queries_count": queries_count
    }

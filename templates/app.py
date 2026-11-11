
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import random
import os
import sys
import tempfile
import subprocess

app = Flask(__name__)
app.secret_key = "placement_portal_secret_key"

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS aptitude_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS coding_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            problem_id INTEGER NOT NULL,
            solved INTEGER NOT NULL DEFAULT 0,
            solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, problem_id),
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            application_date TEXT,
            status TEXT NOT NULL DEFAULT 'Not Applied',
            job_url TEXT,
            notes TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


#  ==================================================
# APTITUDE QUESTIONS
# ==================================================

aptitude_questions = [
    {
        "question": "What is 15% of 200?",
        "options": ["20", "25", "30", "35"],
        "answer": "30"
    },
    {
        "question": "Find the next number: 2, 4, 8, 16, ?",
        "options": ["18", "24", "32", "36"],
        "answer": "32"
    },
    {
        "question": "If 5 pens cost Rs. 50, what is the cost of 1 pen?",
        "options": ["5", "10", "15", "20"],
        "answer": "10"
    }
]
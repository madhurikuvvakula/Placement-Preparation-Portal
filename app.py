
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



aptitude_questions = [
    {
        "question": "A and B can complete a work in 12 days. B and C can complete it in 15 days. A and C can complete it in 20 days. How many days will A, B and C take together?",
        "options": ["8 days", "10 days", "12 days", "15 days"],
        "answer": "10 days"
    },
    {
        "question": "A number is increased by 20% and then decreased by 20%. What is the net percentage change?",
        "options": ["No change", "4% decrease", "4% increase", "2% decrease"],
        "answer": "4% decrease"
    },
    {
        "question": "A train 180 metres long crosses a pole in 9 seconds. What is its speed?",
        "options": ["60 km/hr", "72 km/hr", "80 km/hr", "90 km/hr"],
        "answer": "72 km/hr"
    },
    {
        "question": "The average of 8 numbers is 24. If one number 18 is replaced by 34, what is the new average?",
        "options": ["25", "26", "27", "28"],
        "answer": "26"
    },
    {
        "question": "A shopkeeper marks an item 40% above cost price and gives a discount of 15%. Find the profit percentage.",
        "options": ["15%", "17%", "19%", "21%"],
        "answer": "19%"
    },
    {
        "question": "A sum becomes ₹12,100 in 2 years at 10% compound interest per annum. Find the principal.",
        "options": ["₹9,000", "₹10,000", "₹11,000", "₹12,000"],
        "answer": "₹10,000"
    },
    {
        "question": "Two numbers are in the ratio 3:5. If their sum is 96, find the larger number.",
        "options": ["36", "48", "60", "64"],
        "answer": "60"
    },
    {
        "question": "A bag contains 5 red and 3 blue balls. What is the probability of selecting 2 red balls without replacement?",
        "options": ["5/14", "3/8", "1/2", "5/8"],
        "answer": "5/14"
    },
    {
        "question": "A can complete a work in 18 days and B in 24 days. How long will they take working together?",
        "options": ["9 1/7 days", "10 2/7 days", "12 days", "14 days"],
        "answer": "10 2/7 days"
    },
    {
        "question": "Find the next number: 4, 9, 19, 39, 79, ?",
        "options": ["149", "159", "169", "179"],
        "answer": "159"
    },
    {
        "question": "A person spends 75% of his income. His income increases by 20% and expenditure increases by 10%. What is the percentage increase in savings?",
        "options": ["40%", "45%", "50%", "60%"],
        "answer": "50%"
    },
    {
        "question": "In how many different ways can the letters of the word LEVEL be arranged?",
        "options": ["20", "30", "60", "120"],
        "answer": "30"
    },
    {
        "question": "A car travels 240 km at 60 km/hr and returns at 40 km/hr. Find its average speed for the whole journey.",
        "options": ["45 km/hr", "48 km/hr", "50 km/hr", "52 km/hr"],
        "answer": "48 km/hr"
    },
    {
        "question": "The present ages of A and B are in the ratio 4:5. After 6 years, their ages will be in the ratio 5:6. Find A's present age.",
        "options": ["18 years", "20 years", "24 years", "30 years"],
        "answer": "24 years"
    },
    {
        "question": "If 12 men can complete a work in 15 days, how many men are required to complete the same work in 9 days?",
        "options": ["15", "18", "20", "24"],
        "answer": "20"
    },
    {
        "question": "A number when divided by 7 leaves a remainder of 4. What will be the remainder when its square is divided by 7?",
        "options": ["1", "2", "4", "5"],
        "answer": "2"
    },
    {
        "question": "A mixture contains milk and water in the ratio 5:2. If 14 litres of water is added, the ratio becomes 5:4. Find the original quantity of the mixture.",
        "options": ["42 litres", "49 litres", "56 litres", "63 litres"],
        "answer": "49 litres"
    },
    {
        "question": "A and B invest ₹5,000 and ₹8,000 respectively. After one year, the total profit is ₹3,900. Find B's share.",
        "options": ["₹1,500", "₹2,000", "₹2,400", "₹2,600"],
        "answer": "₹2,400"
    },
    {
        "question": "If 5 machines produce 500 units in 4 hours, how many units will 8 machines produce in 6 hours at the same rate?",
        "options": ["1,000", "1,100", "1,200", "1,400"],
        "answer": "1,200"
    },
    {
        "question": "A clock shows 3:30. What is the smaller angle between the hour and minute hands?",
        "options": ["60°", "75°", "90°", "105°"],
        "answer": "75°"
    }
]

# ==================================================
# PYTHON CODING PROBLEMS
# ==================================================

coding_problems = [
    {
        "id": 1,
        "title": "Print Hello World",
        "rating": "Easy",
        "description": "Print Hello World.",
        "test_cases": [("", "Hello World")]
    },
    {
        "id": 2,
        "title": "Even or Odd",
        "rating": "Easy",
        "description": "Read an integer and print Even or Odd.",
        "test_cases": [("4", "Even"), ("7", "Odd")]
    },
    {
        "id": 3,
        "title": "Add Two Numbers",
        "rating": "Easy",
        "description": "Read two integers and print their sum.",
        "test_cases": [("3\n5", "8"), ("10\n20", "30")]
    },
    {
        "id": 4,
        "title": "Positive, Negative or Zero",
        "rating": "Easy",
        "description": "Read a number and print Positive, Negative or Zero.",
        "test_cases": [("5", "Positive"), ("-3", "Negative"), ("0", "Zero")]
    },
    {
        "id": 5,
        "title": "Largest of Two Numbers",
        "rating": "Easy",
        "description": "Read two integers and print the larger number.",
        "test_cases": [("8\n4", "8"), ("3\n9", "9")]
    },
    {
        "id": 6,
        "title": "Factorial",
        "rating": "Easy",
        "description": "Read n and print n factorial.",
        "test_cases": [("5", "120"), ("0", "1")]
    },
    {
        "id": 7,
        "title": "Multiplication Table",
        "rating": "Easy",
        "description": "Read n and print its multiplication table from 1 to 10, one result per line.",
        "test_cases": [("2", "\n".join(str(2 * i) for i in range(1, 11)))]
    },
    {
        "id": 8,
        "title": "Reverse a Number",
        "rating": "Easy",
        "description": "Read an integer and print its reversed digits.",
        "test_cases": [("1234", "4321"), ("560", "65")]
    },
    {
        "id": 9,
        "title": "Palindrome Number",
        "rating": "Easy",
        "description": "Print Yes if the number is a palindrome; otherwise print No.",
        "test_cases": [("121", "Yes"), ("123", "No")]
    },
    {
        "id": 10,
        "title": "Prime Number",
        "rating": "Medium",
        "description": "Print Yes if the number is prime; otherwise print No.",
        "test_cases": [("7", "Yes"), ("10", "No"), ("1", "No")]
    },
    {
        "id": 11,
        "title": "Fibonacci Sequence",
        "rating": "Medium",
        "description": "Read n and print the first n Fibonacci numbers separated by spaces, starting with 0.",
        "test_cases": [("5", "0 1 1 2 3"), ("1", "0")]
    },
    {
        "id": 12,
        "title": "Sum of Digits",
        "rating": "Easy",
        "description": "Read an integer and print the sum of its digits.",
        "test_cases": [("123", "6"), ("908", "17")]
    },
    {
        "id": 13,
        "title": "Count Vowels",
        "rating": "Easy",
        "description": "Read a line of text and print the number of vowels.",
        "test_cases": [("hello", "2"), ("education", "5")]
    },
    {
        "id": 14,
        "title": "Maximum in a List",
        "rating": "Easy",
        "description": "Read n, then n integers, and print the maximum.",
        "test_cases": [("5\n1 9 3 7 2", "9")]
    },
    {
        "id": 15,
        "title": "Sort a List",
        "rating": "Easy",
        "description": "Read n, then n integers, and print them in ascending order separated by spaces.",
        "test_cases": [("4\n4 1 3 2", "1 2 3 4")]
    },
    {
        "id": 16,
        "title": "Remove Duplicates",
        "rating": "Medium",
        "description": "Read n and n integers. Print unique values in their original order, separated by spaces.",
        "test_cases": [("5\n1 2 1 3 2", "1 2 3")]
    },
    {
        "id": 17,
        "title": "Second Largest Number",
        "rating": "Medium",
        "description": "Read n and n integers. Print the second-largest distinct number. Inputs have at least two distinct values.",
        "test_cases": [("5\n4 1 9 7 9", "7")]
    },
    {
        "id": 18,
        "title": "Anagram Check",
        "rating": "Medium",
        "description": "Read two lines and print Yes if they are anagrams ignoring case and spaces; otherwise print No.",
        "test_cases": [("listen\nsilent", "Yes"), ("hello\nworld", "No")]
    },
    {
        "id": 19,
        "title": "Count Words",
        "rating": "Easy",
        "description": "Read a line of text and print the number of words.",
        "test_cases": [("Hello world", "2"), ("Python is easy", "3")]
    },
    {
        "id": 20,
        "title": "Armstrong Number",
        "rating": "Medium",
        "description": "Print Yes if the non-negative integer is an Armstrong number; otherwise print No.",
        "test_cases": [("153", "Yes"), ("123", "No"), ("0", "Yes")]
    }
]


def get_coding_problem(problem_id):
    for problem in coding_problems:
        if problem["id"] == problem_id:
            return problem
    return None


def get_solved_problem_ids(student_id, conn):
    rows = conn.execute("""
        SELECT problem_id
        FROM coding_progress
        WHERE student_id=? AND solved=1
    """, (student_id,)).fetchall()

    return {row["problem_id"] for row in rows}


def save_problem_progress(student_id, problem_id, solved):
    conn = get_db()

    conn.execute("""
        INSERT INTO coding_progress (student_id, problem_id, solved)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id, problem_id)
        DO UPDATE SET
            solved=MAX(coding_progress.solved, excluded.solved),
            solved_at=CURRENT_TIMESTAMP
    """, (student_id, problem_id, int(solved)))

    conn.commit()
    conn.close()


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():
    if "student_id" in session:
        return redirect("/dashboard")

    return render_template("index.html")


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return "Please fill in all fields.", 400

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO students (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered. Please log in.", 409

        conn.close()
        return redirect("/login")

    return render_template("register.html")


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        student = conn.execute("""
            SELECT id, name, email, password
            FROM students
            WHERE email=? AND password=?
        """, (email, password)).fetchone()

        conn.close()

        if student:
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            return redirect("/dashboard")

        return "Invalid email or password. Please try again.", 401

    return render_template("login.html")


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect("/login")

    student_id = session["student_id"]
    conn = get_db()

    latest_score = conn.execute("""
        SELECT score
        FROM aptitude_scores
        WHERE student_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (student_id,)).fetchone()

    aptitude_score = latest_score["score"] if latest_score else 0

    test_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM aptitude_scores
        WHERE student_id=?
    """, (student_id,)).fetchone()["count"]

    progress_scores = conn.execute("""
        SELECT score
        FROM aptitude_scores
        WHERE student_id=?
        ORDER BY id ASC
    """, (student_id,)).fetchall()

    scores = [row["score"] for row in progress_scores]

    coding_solved = conn.execute("""
        SELECT COUNT(*) AS count
        FROM coding_progress
        WHERE student_id=? AND solved=1
    """, (student_id,)).fetchone()["count"]

    coding_total = len(coding_problems)
    coding_remaining = max(0, coding_total - coding_solved)

    coding_progress = (
        int(coding_solved / coding_total * 100)
        if coding_total else 0
    )

    job_total = conn.execute("""
        SELECT COUNT(*) AS count FROM jobs WHERE student_id=?
    """, (student_id,)).fetchone()["count"]

    job_applied = conn.execute("""
        SELECT COUNT(*) AS count FROM jobs
        WHERE student_id=? AND status='Applied'
    """, (student_id,)).fetchone()["count"]

    job_interview = conn.execute("""
        SELECT COUNT(*) AS count FROM jobs
        WHERE student_id=? AND status='Interview'
    """, (student_id,)).fetchone()["count"]

    job_selected = conn.execute("""
        SELECT COUNT(*) AS count FROM jobs
        WHERE student_id=? AND status='Selected'
    """, (student_id,)).fetchone()["count"]

    job_rejected = conn.execute("""
        SELECT COUNT(*) AS count FROM jobs
        WHERE student_id=? AND status='Rejected'
    """, (student_id,)).fetchone()["count"]

    conn.close()

    return render_template(
        "dashboard.html",
        name=session.get("student_name", "Student"),
        aptitude_score=aptitude_score,
        test_count=test_count,
        progress_scores=scores,
        coding_solved=coding_solved,
        coding_total=coding_total,
        coding_remaining=coding_remaining,
        coding_progress=coding_progress,
        job_total=job_total,
        job_applied=job_applied,
        job_interview=job_interview,
        job_selected=job_selected,
        job_rejected=job_rejected
    )



# ==================================================
# APTITUDE TEST
# ==================================================

@app.route("/aptitude")
def aptitude():
    if "student_id" not in session:
        return redirect("/login")

    return render_template("aptitude.html")


@app.route("/test", methods=["GET", "POST"])
def test():
    if "student_id" not in session:
        return redirect("/login")

    if request.method == "GET":
        questions = random.sample(aptitude_questions, 5)

        session["aptitude_test"] = [
            aptitude_questions.index(question)
            for question in questions
        ]

        return render_template("test.html", questions=questions)

    question_ids = session.pop("aptitude_test", None)

    if not question_ids:
        return redirect("/aptitude")

    score = 0

    for position, question_id in enumerate(question_ids):
        question = aptitude_questions[question_id]

        answer = request.form.get(f"q{position}", "").strip()
        correct_answer = str(question["answer"]).strip()

        if answer == correct_answer:
            score += 1

    conn = get_db()

    conn.execute("""
        INSERT INTO aptitude_scores (student_id, score)
        VALUES (?, ?)
    """, (session["student_id"], score))

    conn.commit()
    conn.close()

    return render_template("result.html", score=score)


# ==================================================
# CODING PRACTICE LIST
# ==================================================


@app.route("/coding")
def coding():
    if "student_id" not in session:
        return redirect("/login")

    conn = get_db()
    solved_ids = get_solved_problem_ids(session["student_id"], conn)
    conn.close()

    problems = []

    for problem in coding_problems:
        item = problem.copy()

        # Template expects "difficulty", but problem data uses "rating"
        item["difficulty"] = item.get("rating", "Easy")
        item["solved"] = item["id"] in solved_ids

        problems.append(item)

    total_count = len(coding_problems)
    solved_count = sum(1 for p in problems if p["solved"])
    remaining_count = total_count - solved_count

    progress_percent = (
        int(solved_count / total_count * 100)
        if total_count else 0
    )

    return render_template(
        "coding.html",
        problems=problems,
        solved_ids=solved_ids,
        solved_count=solved_count,
        total_count=total_count,
        remaining_count=remaining_count,
        progress_percent=progress_percent
    )

# ==================================================
# CODING PROBLEM AND SUBMISSION
# ==================================================


@app.route("/coding/<int:problem_id>", methods=["GET", "POST"])
def coding_problem(problem_id):
    if "student_id" not in session:
        return redirect("/login")

    problem = get_coding_problem(problem_id)

    if problem is None:
        return "Coding problem not found.", 404

    result = None
    message = None
    results = []
    passed_count = 0
    total_tests = len(problem["test_cases"])
    source_code = ""
    language = "python"

    if request.method == "POST":
        source_code = request.form.get("code", "").strip()
        language = request.form.get("language", "python").lower()

        if language not in ["python", "c", "cpp"]:
            message = "Please select a supported language."
        elif not source_code:
            message = "Please enter your code."
        else:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    if language == "python":
                        file_path = os.path.join(temp_dir, "solution.py")
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(source_code)
                        command = [sys.executable, "-I", file_path]

                    elif language == "c":
                        file_path = os.path.join(temp_dir, "solution.c")
                        exe_path = os.path.join(temp_dir, "solution.exe")
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(source_code)

                        compile_result = subprocess.run(
                            ["gcc", file_path, "-o", exe_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if compile_result.returncode != 0:
                            raise Exception(compile_result.stderr[:1500])

                        command = [exe_path]

                    else:
                        file_path = os.path.join(temp_dir, "solution.cpp")
                        exe_path = os.path.join(temp_dir, "solution.exe")
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(source_code)

                        compile_result = subprocess.run(
                            ["g++", file_path, "-o", exe_path],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if compile_result.returncode != 0:
                            raise Exception(compile_result.stderr[:1500])

                        command = [exe_path]

                    for test_input, expected_output in problem["test_cases"]:
                        completed = subprocess.run(
                            command,
                            input=test_input,
                            text=True,
                            capture_output=True,
                            timeout=3,
                            cwd=temp_dir
                        )

                        actual = " ".join(completed.stdout.split())
                        expected = " ".join(expected_output.split())

                        passed = (
                            completed.returncode == 0
                            and actual == expected
                        )

                        results.append({
                            "input": test_input,
                            "expected": expected_output,
                            "actual": completed.stdout.strip()
                                if completed.stdout else completed.stderr[:1500],
                            "passed": passed
                        })

                        if passed:
                            passed_count += 1
                        else:
                            if completed.returncode != 0:
                                message = completed.stderr[:1500]
                            break

                if passed_count == total_tests and total_tests > 0:
                    save_problem_progress(
                        session["student_id"],
                        problem_id,
                        True
                    )
                    result = "passed"
                    message = "Correct! All test cases passed."
                else:
                    result = "failed"
                    if not message:
                        message = "Some test cases failed."

            except subprocess.TimeoutExpired:
                result = "failed"
                message = "Your program exceeded the time limit."
            except Exception as exc:
                result = "failed"
                message = str(exc)

    conn = get_db()
    solved_ids = get_solved_problem_ids(session["student_id"], conn)
    conn.close()

    return render_template(
        "coding_problem.html",
        problem=problem,
        solved=problem_id in solved_ids,
        result=result,
        message=message,
        results=results,
        passed_count=passed_count,
        total_tests=total_tests,
        code=source_code,
        language=language
    )
# ==================================================
# JOB TRACKER - LIST
# ==================================================

@app.route("/jobs")
def jobs():
    if "student_id" not in session:
        return redirect("/login")

    conn = get_db()

    job_list = conn.execute("""
        SELECT * FROM jobs
        WHERE student_id=?
        ORDER BY id DESC
    """, (session["student_id"],)).fetchall()

    conn.close()

    return render_template("jobs.html", jobs=job_list)

# ==================================================
# JOB TRACKER - EDIT
# ==================================================

@app.route("/jobs/edit/<int:job_id>", methods=["GET", "POST"])
def edit_job(job_id):
    if "student_id" not in session:
        return redirect("/login")

    conn = get_db()

    job = conn.execute("""
        SELECT *
        FROM jobs
        WHERE id=? AND student_id=?
    """, (job_id, session["student_id"])).fetchone()

    if job is None:
        conn.close()
        return "Job not found.", 404

    if request.method == "POST":
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        application_date = request.form.get("application_date", "")
        status = request.form.get("status", "Not Applied")
        job_url = request.form.get("job_url", "").strip()
        notes = request.form.get("notes", "").strip()

        allowed_statuses = {
            "Not Applied", "Applied", "Online Test",
            "Interview", "Selected", "Rejected"
        }

        if not company or not role:
            conn.close()
            return "Company and role are required.", 400

        if status not in allowed_statuses:
            status = "Not Applied"

        conn.execute("""
            UPDATE jobs
            SET company=?, role=?, application_date=?,
                status=?, job_url=?, notes=?
            WHERE id=? AND student_id=?
        """, (
            company, role, application_date,
            status, job_url, notes,
            job_id, session["student_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/jobs")

    conn.close()

    return render_template("edit_job.html", job=job)


# ==================================================
# JOB TRACKER - DELETE
# ==================================================

@app.route("/jobs/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    if "student_id" not in session:
        return redirect("/login")

    conn = get_db()

    conn.execute("""
        DELETE FROM jobs
        WHERE id=? AND student_id=?
    """, (job_id, session["student_id"]))

    conn.commit()
    conn.close()

    return redirect("/jobs")


# ==================================================
# START APPLICATION
# ==================================================

create_database()

if __name__ == "__main__":
    app.run(debug=True)

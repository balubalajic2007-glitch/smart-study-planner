import sqlite3
from datetime import datetime, date, timedelta

DB_NAME = "smart_study.db"


# =========================================================
# DATABASE
# =========================================================

def connect_db():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            difficulty INTEGER NOT NULL,
            exam_date TEXT NOT NULL,
            study_hours REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# DIFFICULTY
# =========================================================

def difficulty_name(value):
    if value == 1:
        return "Easy"
    elif value == 2:
        return "Medium"
    else:
        return "Hard"


def get_difficulty():
    while True:
        print("\nDifficulty:")
        print("1. Easy")
        print("2. Medium")
        print("3. Hard")

        choice = input("Choose: ").strip()

        if choice in ["1", "2", "3"]:
            return int(choice)

        print("Invalid choice.")


# =========================================================
# ADD SUBJECT
# =========================================================

def add_subject():
    print("\n========== ADD SUBJECT ==========")

    name = input("Subject name: ").strip()

    if not name:
        print("Subject name cannot be empty.")
        return

    difficulty = get_difficulty()

    while True:
        exam_date = input(
            "Exam date (YYYY-MM-DD): "
        ).strip()

        try:
            exam = datetime.strptime(
                exam_date, "%Y-%m-%d"
            ).date()

            if exam < date.today():
                print("Exam date cannot be in the past.")
                continue

            break

        except ValueError:
            print("Invalid date format.")

    while True:
        try:
            hours = float(
                input("Available study hours per week: ")
            )

            if hours <= 0:
                print("Hours must be greater than 0.")
                continue

            break

        except ValueError:
            print("Enter a valid number.")

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO subjects
            (name, difficulty, exam_date, study_hours)
            VALUES (?, ?, ?, ?)
        """, (
            name,
            difficulty,
            exam_date,
            hours
        ))

        conn.commit()

        print(f"\n✅ {name} added successfully.")

    except sqlite3.IntegrityError:
        print("\n⚠️ Subject already exists.")

    conn.close()


# =========================================================
# REMOVE SUBJECT
# =========================================================

def remove_subject():
    print("\n========== REMOVE SUBJECT ==========")

    show_subjects()

    try:
        subject_id = int(
            input("\nEnter subject ID: ")
        )
    except ValueError:
        print("Invalid ID.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM subjects WHERE id = ?",
        (subject_id,)
    )

    subject = cursor.fetchone()

    if not subject:
        print("Subject not found.")
        conn.close()
        return

    cursor.execute(
        "DELETE FROM topics WHERE subject_id = ?",
        (subject_id,)
    )

    cursor.execute(
        "DELETE FROM subjects WHERE id = ?",
        (subject_id,)
    )

    conn.commit()
    conn.close()

    print(f"✅ {subject[0]} removed.")


# =========================================================
# SHOW SUBJECTS
# =========================================================

def show_subjects():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, difficulty, exam_date, study_hours
        FROM subjects
        ORDER BY exam_date
    """)

    subjects = cursor.fetchall()

    conn.close()

    print("\n========== SUBJECTS ==========")

    if not subjects:
        print("No subjects found.")
        return

    for subject in subjects:

        sid, name, difficulty, exam_date, hours = subject

        exam = datetime.strptime(
            exam_date, "%Y-%m-%d"
        ).date()

        days_left = (exam - date.today()).days

        print(
            f"\nID: {sid}"
            f"\nSubject: {name}"
            f"\nDifficulty: {difficulty_name(difficulty)}"
            f"\nExam: {exam_date}"
            f"\nDays left: {days_left}"
            f"\nWeekly hours: {hours}"
        )


# =========================================================
# ADD TOPIC
# =========================================================

def add_topic():
    print("\n========== ADD TOPIC ==========")

    show_subjects()

    try:
        subject_id = int(
            input("\nEnter subject ID: ")
        )
    except ValueError:
        print("Invalid ID.")
        return

    topic_name = input(
        "Enter topic name: "
    ).strip()

    if not topic_name:
        print("Topic cannot be empty.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM subjects WHERE id = ?",
        (subject_id,)
    )

    subject = cursor.fetchone()

    if not subject:
        print("Subject not found.")
        conn.close()
        return

    cursor.execute("""
        INSERT INTO topics
        (subject_id, topic_name)
        VALUES (?, ?)
    """, (
        subject_id,
        topic_name
    ))

    conn.commit()
    conn.close()

    print("✅ Topic added.")


# =========================================================
# SHOW TOPICS
# =========================================================

def show_topics():
    print("\n========== TOPICS ==========")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            topics.id,
            subjects.name,
            topics.topic_name,
            topics.completed
        FROM topics
        JOIN subjects
        ON topics.subject_id = subjects.id
        ORDER BY subjects.name
    """)

    topics = cursor.fetchall()

    conn.close()

    if not topics:
        print("No topics found.")
        return

    for topic in topics:

        tid, subject, name, completed = topic

        status = "✅ Completed" if completed else "⏳ Pending"

        print(
            f"{tid}. {subject} → "
            f"{name} → {status}"
        )


# =========================================================
# MARK TOPIC COMPLETE
# =========================================================

def mark_topic_complete():
    show_topics()

    try:
        topic_id = int(
            input("\nEnter topic ID: ")
        )
    except ValueError:
        print("Invalid ID.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE topics
        SET completed = 1
        WHERE id = ?
    """, (topic_id,))

    conn.commit()

    if cursor.rowcount == 0:
        print("Topic not found.")
    else:
        print("✅ Topic marked as completed.")

    conn.close()


# =========================================================
# CALCULATE PRIORITY
# =========================================================

def calculate_priority(difficulty, exam_date):

    exam = datetime.strptime(
        exam_date, "%Y-%m-%d"
    ).date()

    days_left = max(
        1,
        (exam - date.today()).days
    )

    # Higher difficulty = higher priority
    difficulty_score = difficulty * 10

    # Nearer exam = higher priority
    urgency_score = max(
        1,
        30 / days_left
    )

    return difficulty_score + urgency_score


# =========================================================
# GENERATE WEEKLY PLAN
# =========================================================

def generate_weekly_plan():

    print("\n========== WEEKLY STUDY PLAN ==========")

    try:
        daily_hours = float(
            input(
                "How many hours can you study per day? "
            )
        )

        if daily_hours <= 0:
            print("Hours must be greater than 0.")
            return

    except ValueError:
        print("Invalid number.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            difficulty,
            exam_date,
            study_hours
        FROM subjects
    """)

    subjects = cursor.fetchall()

    conn.close()

    if not subjects:
        print("Add subjects first.")
        return

    subjects_with_priority = []

    for subject in subjects:

        sid, name, difficulty, exam_date, hours = subject

        priority = calculate_priority(
            difficulty,
            exam_date
        )

        subjects_with_priority.append(
            (
                sid,
                name,
                difficulty,
                exam_date,
                priority
            )
        )

    subjects_with_priority.sort(
        key=lambda x: x[4],
        reverse=True
    )

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]

    print()

    for i, day in enumerate(days):

        subject = subjects_with_priority[
            i % len(subjects_with_priority)
        ]

        sid, name, difficulty, exam_date, priority = subject

        print(
            f"{day:<10} → "
            f"{name:<15} "
            f"| {daily_hours} hour(s) "
            f"| Priority: {priority:.2f}"
        )


# =========================================================
# UPCOMING EXAMS
# =========================================================

def upcoming_exams():

    print("\n========== UPCOMING EXAMS ==========")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, difficulty, exam_date
        FROM subjects
        ORDER BY exam_date
    """)

    subjects = cursor.fetchall()

    conn.close()

    if not subjects:
        print("No exams available.")
        return

    for name, difficulty, exam_date in subjects:

        exam = datetime.strptime(
            exam_date, "%Y-%m-%d"
        ).date()

        days_left = (
            exam - date.today()
        ).days

        if days_left >= 0:

            print(
                f"{name:<15} | "
                f"{exam_date} | "
                f"{days_left} days left | "
                f"{difficulty_name(difficulty)}"
            )


# =========================================================
# PROGRESS
# =========================================================

def show_progress():

    print("\n========== STUDY PROGRESS ==========")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            subjects.name,
            COUNT(topics.id),
            SUM(topics.completed)
        FROM subjects
        LEFT JOIN topics
        ON subjects.id = topics.subject_id
        GROUP BY subjects.id
    """)

    data = cursor.fetchall()

    conn.close()

    if not data:
        print("No subjects available.")
        return

    total_all = 0
    completed_all = 0

    for name, total, completed in data:

        completed = completed or 0

        if total > 0:
            percentage = (
                completed / total
            ) * 100
        else:
            percentage = 0

        total_all += total
        completed_all += completed

        print(
            f"\n{name}"
            f"\nTopics: {total}"
            f"\nCompleted: {completed}"
            f"\nProgress: {percentage:.1f}%"
        )

        bar_length = int(
            percentage / 10
        )

        print(
            "[" +
            "█" * bar_length +
            "-" * (10 - bar_length) +
            "]"
        )

    if total_all > 0:

        overall = (
            completed_all /
            total_all
        ) * 100

        print(
            f"\nOverall Progress: "
            f"{overall:.1f}%"
        )


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():

    print("\n" + "=" * 50)
    print("        SMART STUDY PLANNER")
    print("=" * 50)

    show_subjects()
    upcoming_exams()
    show_progress()


# =========================================================
# MAIN MENU
# =========================================================

def main():

    create_tables()

    # Add your example subjects automatically
    # only if database is empty.
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM subjects"
    )

    count = cursor.fetchone()[0]

    conn.close()

    if count == 0:

        print("\nAdding example subjects...")

        example_subjects = [
            ("DSA", 3, 15, 8),
            ("OS", 2, 10, 6),
            ("Mathematics", 3, 7, 8),
            ("English", 1, 20, 3),
            ("DDCO", 3, 12, 7),
            ("Java", 3, 18, 8)
        ]

        for name, difficulty, days, hours in example_subjects:

            exam_date = (
                date.today() +
                timedelta(days=days)
            ).strftime("%Y-%m-%d")

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO subjects
                (name, difficulty, exam_date, study_hours)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                difficulty,
                exam_date,
                hours
            ))

            conn.commit()
            conn.close()

    while True:

        print("\n")
        print("=" * 50)
        print("             MAIN MENU")
        print("=" * 50)

        print("1. Dashboard")
        print("2. Add Subject")
        print("3. Remove Subject")
        print("4. Show Subjects")
        print("5. Add Topic")
        print("6. Show Topics")
        print("7. Mark Topic Completed")
        print("8. Generate Weekly Study Plan")
        print("9. Show Upcoming Exams")
        print("10. Show Study Progress")
        print("0. Exit")

        choice = input(
            "\nEnter your choice: "
        ).strip()

        if choice == "1":
            dashboard()

        elif choice == "2":
            add_subject()

        elif choice == "3":
            remove_subject()

        elif choice == "4":
            show_subjects()

        elif choice == "5":
            add_topic()

        elif choice == "6":
            show_topics()

        elif choice == "7":
            mark_topic_complete()

        elif choice == "8":
            generate_weekly_plan()

        elif choice == "9":
            upcoming_exams()

        elif choice == "10":
            show_progress()

        elif choice == "0":
            print("\nThank you for using Smart Study Planner!")
            break

        else:
            print("\n❌ Invalid choice.")


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":
    main()
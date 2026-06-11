from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "library_secret_key"

# Database Connection configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "1212",  # <-- CHANGE TO YOUR MYSQL PASSWORD
    "database": "library_management"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

# Books Catalog View
@app.route('/books')
def books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Book")
    books_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('books.html', books=books_data)

# Authors Registry View
@app.route('/authors')
def authors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Author")
    authors_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('authors.html', authors=authors_data)

# Book Issue Operations Desk (Triggers Procedure 1 & Trigger 1)
@app.route('/issue', methods=['GET', 'POST'])
def issue():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        issue_id = request.form['issue_id']
        member_id = request.form['member_id']
        book_id = request.form['book_id']
        issue_date = request.form['issue_date']
        due_date = request.form['due_date']
        
        try:
            # Calls your Stored Procedure "IssueBook"
            cursor.callproc("IssueBook", (issue_id, member_id, book_id, issue_date, due_date))
            conn.commit()
            flash("Book issued successfully! Status automatically updated to 'Issued' via Trigger.", "success")
        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
        return redirect(url_for('issue'))

    cursor.execute("SELECT * FROM Issue")
    issues_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('issue.html', issues=issues_data)

# Book Returns & Fines Desk (Fires Trigger 2 for calculating late parameters)
@app.route('/fines', methods=['GET', 'POST'])
def fines():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        issue_id = request.form['issue_id']
        return_date = request.form['return_date']
        
        try:
            # Updating return date fires Trigger 2 (trg_fine)
            cursor.execute("UPDATE Issue SET return_date = %s WHERE issue_id = %s", (return_date, issue_id))
            
            # Revert availability status back to safe warehouse tracking state
            cursor.execute("SELECT book_id FROM Issue WHERE issue_id = %s", (issue_id,))
            record = cursor.fetchone()
            if record:
                cursor.execute("UPDATE Book SET availability = 'Available' WHERE book_id = %s", (record['book_id'],))
            
            conn.commit()
            flash("Return registered successfully! Overdue fines calculated automatically.", "success")
        except mysql.connector.Error as err:
            flash(f"Transaction Error: {err}", "danger")
        return redirect(url_for('fines'))

    cursor.execute("SELECT * FROM Fine")
    fines_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('fines.html', fines=fines_data)

# Library Staff Directory Roster
@app.route('/staff')
def staff():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Staff")
    staff_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff.html', staff=staff_data)

# Assignment Queries Analytics Center (Complex Joins & Subqueries)
@app.route('/analytics')
def analytics():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    queries_output = {}

    # Query 3: 2-Table INNER JOIN
    cursor.execute("SELECT i.issue_id, m.name, i.book_id, i.issue_date FROM Issue i INNER JOIN Member m ON i.member_id = m.member_id")
    queries_output['q3'] = cursor.fetchall()

    # Query 4: 3-Table JOIN
    cursor.execute("SELECT i.issue_id, m.name as member_name, b.title as book_title, i.issue_date FROM Issue i JOIN Member m ON i.member_id = m.member_id JOIN Book b ON i.book_id = b.book_id")
    queries_output['q4'] = cursor.fetchall()

    # Query 5: GROUP BY Category
    cursor.execute("SELECT category, COUNT(*) AS TotalBooks FROM Book GROUP BY category")
    queries_output['q5'] = cursor.fetchall()

    # Query 6: HAVING Category > 50
    cursor.execute("SELECT category, COUNT(*) AS TotalBooks FROM Book GROUP BY category HAVING COUNT(*) > 50")
    queries_output['q6'] = cursor.fetchall()

    # Query 7: Subquery Average Price
    cursor.execute("SELECT * FROM Book WHERE price > (SELECT AVG(price) FROM Book)")
    queries_output['q7'] = cursor.fetchall()

    # Query 10: NOT EXISTS Unissued Stock
    cursor.execute("SELECT * FROM Book b WHERE NOT EXISTS (SELECT * FROM Issue i WHERE b.book_id = i.book_id)")
    queries_output['q10'] = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('analytics.html', data=queries_output)

if __name__ == '__main__':
    app.run(debug=True)
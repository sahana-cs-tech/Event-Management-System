from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
from db_config import db, cursor

app = Flask(__name__)
app.secret_key = "event123"
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():

    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM registrations")
    registrations = cursor.fetchone()[0]

    return render_template(
        "index.html",
        events=events,
        users=users,
        total_events=total_events,
        registrations=registrations
    )


# LOGIN

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = """
        SELECT *
        FROM users
        WHERE email=%s AND password=%s
        """

        cursor.execute(sql, (email, password))
        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]      # role column

            return redirect(url_for('dashboard'))

        return "Invalid Login"

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Total Events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    # My Registrations
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM registrations
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )

    my_events = cursor.fetchone()[0]

    return render_template(
        'dashboard.html',
        role=session.get('role'),
        name=session.get('name'),
        total_events=total_events,
        my_events=my_events
    )


# REGISTER USER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        sql = """
        INSERT INTO users(name,email,password)
        VALUES(%s,%s,%s)
        """

        cursor.execute(sql, (name, email, password))
        db.commit()

        # Auto login after signup
        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        session['user_id'] = user[0]
        session['name'] = user[1]
        session['role'] = user[4]

        return redirect(url_for('dashboard'))

    return render_template('register.html')


# SHOW EVENTS
@app.route('/events')
def events():

    search = request.args.get('search')
    category = request.args.get('category')

    sql = """
    SELECT *
    FROM events
    WHERE 1=1
    """

    values = []

    if search:

        sql += """
        AND event_name LIKE %s
        """

        values.append(
            '%' + search + '%'
        )

    if category:

        sql += """
        AND category_id=%s
        """

        values.append(category)

    cursor.execute(sql, tuple(values))

    events_data = cursor.fetchall()

    cursor.execute(
        """
        SELECT *
        FROM categories
        """
    )

    categories = cursor.fetchall()

    return render_template(
        'events.html',
        events=events_data,
        categories=categories
    )
@app.route('/event/<int:event_id>')
def event_details(event_id):

    cursor.execute(
        """
        SELECT *
        FROM events
        WHERE event_id=%s
        """,
        (event_id,)
    )

    event = cursor.fetchone()

    return render_template(
        'event_details.html',
        event=event
    )

# CREATE EVENT
@app.route('/create_event', methods=['GET', 'POST'])
def create_event():

    if session.get('role') != 'admin':
        return "Access Denied: Only Admin can create events"

    if request.method == 'POST':

        event_name = request.form['event_name']
        description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        venue = request.form['venue']
        total_seats = request.form['total_seats']
        category_id = request.form['category_id']
        image = request.files['image']
        filename = secure_filename(image.filename)

        image.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )
        sql = """
       INSERT INTO events
       (
            event_name,
            description,
            event_date,
            event_time,
            venue,
            total_seats,
            available_seats,
            category_id,
            image
        )   
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(
            sql,
            (
                event_name,
                description,
                event_date,
                event_time,
                venue,
                total_seats,
                total_seats,
                category_id,
                filename
            )
        )

        db.commit()

        return redirect(url_for('events'))

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    return render_template(
        'create_event.html',
        categories=categories
    )
@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):

    if session.get('role') != 'admin':
        return "Access Denied"

    if request.method == 'POST':

        event_name = request.form['event_name']
        description = request.form['description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        venue = request.form['venue']
        total_seats = request.form['total_seats']

        cursor.execute(
            """
            UPDATE events
            SET
                event_name=%s,
                description=%s,
                event_date=%s,
                event_time=%s,
                venue=%s,
                total_seats=%s
            WHERE event_id=%s
            """,
            (
                event_name,
                description,
                event_date,
                event_time,
                venue,
                total_seats,
                event_id
            )
        )

        db.commit()

        return redirect(url_for('events'))

    cursor.execute(
        "SELECT * FROM events WHERE event_id=%s",
        (event_id,)
    )

    event = cursor.fetchone()

    return render_template(
        "edit_event.html",
        event=event
    )
@app.route('/delete_event/<int:event_id>')
def delete_event(event_id):

    if session.get('role') != 'admin':
        return "Access Denied"

    cursor.execute(
        """
        DELETE FROM registrations
        WHERE event_id=%s
        """,
        (event_id,)
    )

    cursor.execute(
        """
        DELETE FROM events
        WHERE event_id=%s
        """,
        (event_id,)
    )

    db.commit()

    return redirect(url_for('events'))
# LOGOUT
@app.route('/logout')
def logout():

    session.clear()
    return redirect(url_for('login'))

@app.route('/register_event/<int:event_id>')
def register_event(event_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor.execute(
        """
        SELECT *
        FROM registrations
        WHERE user_id=%s
        AND event_id=%s
        """,
        (user_id, event_id)
    )

    

    # Check duplicate registration

    cursor.execute(
        """
        SELECT *
        FROM registrations
        WHERE user_id=%s
        AND event_id=%s
        """,
        (user_id, event_id)
    )

    existing = cursor.fetchone()

    if existing:
        return render_template(
            'error.html',
            message="You have already registered for this event."
        )

    # Check available seats

    cursor.execute(
        """
        SELECT available_seats
        FROM events
        WHERE event_id=%s
        """,
        (event_id,)
    )

    seats = cursor.fetchone()

    if seats[0] <= 0:
        return render_template(
            'error.html',
            message="Sorry! This event is full."
        )

    # Register user

    cursor.execute(
        """
        INSERT INTO registrations(user_id,event_id)
        VALUES(%s,%s)
        """,
        (user_id, event_id)
    )

    # Reduce seats

    cursor.execute(
        """
        UPDATE events
        SET available_seats = available_seats - 1
        WHERE event_id=%s
        """,
        (event_id,)
    )

    db.commit()

    cursor.execute(
        """
        SELECT *
        FROM events
        WHERE event_id=%s
        """,
        (event_id,)
    )

    event = cursor.fetchone()

    return render_template(
        "success.html",
        event=event
    )
@app.route('/my_events')
def my_events():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    sql = """
    SELECT
    e.event_id,
    e.event_name
    FROM registrations r
    JOIN events e
    ON r.event_id = e.event_id
    WHERE r.user_id = %s
    """

    cursor.execute(sql, (user_id,))
    data = cursor.fetchall()

    return render_template(
        'my_events.html',
        events=data
    )
@app.route('/reports')
def reports():

    if session.get('role') != 'admin':
        return "Access Denied"

    # Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Total Events
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]

    # Total Registrations
    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_registrations = cursor.fetchone()[0]

    # Most Popular Event
    cursor.execute("""
        SELECT
        e.event_name,
        COUNT(*) AS total
        FROM registrations r
        JOIN events e
        ON r.event_id = e.event_id
        GROUP BY e.event_name
        ORDER BY total DESC
        LIMIT 1
    """)

    popular_event = cursor.fetchone()

    return render_template(
        'reports.html',
        total_users=total_users,
        total_events=total_events,
        total_registrations=total_registrations,
        popular_event=popular_event
    )
@app.route('/feedback/<int:event_id>', methods=['GET', 'POST'])
def feedback(event_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        rating = request.form['rating']
        comments = request.form['comments']

        # CHECK IF FEEDBACK ALREADY EXISTS

        cursor.execute(
            """
            SELECT *
            FROM feedback
            WHERE user_id=%s
            AND event_id=%s
            """,
            (session['user_id'], event_id)
        )

        existing = cursor.fetchone()

        if existing:
            return "Feedback already submitted for this event."

        # INSERT NEW FEEDBACK

        sql = """
        INSERT INTO feedback
        (
            user_id,
            event_id,
            rating,
            comments
        )
        VALUES
        (%s,%s,%s,%s)
        """

        cursor.execute(
            sql,
            (
                session['user_id'],
                event_id,
                rating,
                comments
            )
        )

        db.commit()

        return "Feedback Submitted Successfully!"

    return render_template('feedback.html')
@app.route('/analytics')
def analytics():

    if session.get('role') != 'admin':
        return "Access Denied"

    # Total Users

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_users = cursor.fetchone()[0]

    # Total Events

    cursor.execute(
        "SELECT COUNT(*) FROM events"
    )

    total_events = cursor.fetchone()[0]

    # Total Registrations

    cursor.execute(
        "SELECT COUNT(*) FROM registrations"
    )

    total_registrations = cursor.fetchone()[0]

    # Most Popular Event

    cursor.execute(
        """
        SELECT
        e.event_name,
        COUNT(r.registration_id) AS total
        FROM events e
        LEFT JOIN registrations r
        ON e.event_id = r.event_id
        GROUP BY e.event_id
        ORDER BY total DESC
        LIMIT 1
        """
    )

    popular_event = cursor.fetchone()

    # Average Rating

    cursor.execute(
        """
        SELECT ROUND(AVG(rating),2)
        FROM feedback
        """
    )

    avg_rating = cursor.fetchone()[0]

    return render_template(
        'analytics.html',
        total_users=total_users,
        total_events=total_events,
        total_registrations=total_registrations,
        popular_event=popular_event,
        avg_rating=avg_rating
    )

# RUN APP
if __name__ == "__main__":
    app.run(debug=True)
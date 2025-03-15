from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
TA_CODE = '1234'

# Add enumerate to the template context
@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

# Initialize database
def init_db():
    with sqlite3.connect('points.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS teams (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT UNIQUE,
                     total_points INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS points (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     team_id INTEGER,
                     points INTEGER,
                     reason TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (team_id) REFERENCES teams (id))''')
        conn.commit()

@app.route('/')
def leaderboard():
    with sqlite3.connect('points.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, total_points FROM teams ORDER BY total_points DESC")
        teams = c.fetchall()
    return render_template('leaderboard.html', teams=teams)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ta_code = request.form['ta_code']
        if ta_code == TA_CODE:
            session['is_ta'] = True
            return redirect(url_for('add_points'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_ta', None)
    return redirect(url_for('leaderboard'))

@app.route('/add_points', methods=['GET', 'POST'])
def add_points():
    if 'is_ta' not in session:
        return redirect(url_for('login'))
    
    with sqlite3.connect('points.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM teams")
        teams = c.fetchall()
    
    if request.method == 'POST':
        team_id = request.form['team_id']
        points = int(request.form['points'])
        reason = request.form['reason']
        with sqlite3.connect('points.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO points (team_id, points, reason) VALUES (?, ?, ?)",
                      (team_id, points, reason))
            c.execute("UPDATE teams SET total_points = total_points + ? WHERE id = ?",
                      (points, team_id))
            conn.commit()
        return redirect(url_for('leaderboard'))
    
    return render_template('add_points.html', teams=teams)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

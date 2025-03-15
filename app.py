from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
TA_CODE = '1234'

TEAMS = [
    "Team 1 (Game Changers)",
    "Team 2 (Ctrl-Alt-Defeat)",
    "Team 3 (Sunny Side Studios)",
    "Team 4 (Green Games Studio)",
    "Team 5 (Catioca)",
    "Team 6 (Mycrosoffed Studios)",
    "Team 7 (Lucky Seven Studios)",
    "Team 8 (The Cat Coders)",
    "Team 9 (Terra Ninja Studios)"
]

@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

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
        
        for team_name in TEAMS:
            c.execute("INSERT OR IGNORE INTO teams (name, total_points) VALUES (?, 0)", (team_name,))
        
        conn.commit()

@app.route('/')
def leaderboard():
    with sqlite3.connect('points.db') as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, total_points FROM teams ORDER BY total_points DESC")
        teams = c.fetchall()
    return render_template('leaderboard.html', teams=teams)

@app.route('/team_history/<int:team_id>')
def team_history(team_id):
    with sqlite3.connect('points.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
        team_name = c.fetchone()[0]
        
        c.execute("""
            SELECT points, reason, timestamp 
            FROM points 
            WHERE team_id = ? 
            ORDER BY timestamp DESC
        """, (team_id,))
        history = c.fetchall()
    
    return render_template('team_history.html', team_name=team_name, history=history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ta_code = request.form['ta_code']
        if ta_code == TA_CODE:
            session['is_ta'] = True
            return redirect(url_for('add_points'))
        else:
            flash('Invalid TA code', 'danger')
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
        c.execute("SELECT id, name FROM teams ORDER BY name")
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
            
        flash(f'Added {points} points successfully!', 'success')
        return redirect(url_for('leaderboard'))
    
    return render_template('add_points.html', teams=teams)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

import sqlite3
import os
import random
import string
import datetime
import sys
import io
import requests
from flask import Flask, request, g, redirect, abort, render_template_string, send_file, url_for

app = Flask(__name__)
DATABASE = 'cutlist.db'

# HTML template for the main layout to keep it simple and procedural.
LAYOUT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cutlist - URL Shortener</title>
    <style>
        body { font-family: system-ui, sans-serif; background-color: #f7f7f7; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px; width: 100%; text-align: center; }
        input[type="text"], input[type="url"] { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .error { color: red; margin-bottom: 10px; }
        .success { color: green; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="card">
        <h1>✂️ Cutlist</h1>
        {{ content|safe }}
        <div style="margin-top: 20px; font-size: 0.9em;">
            <a href="/">Home</a> | <a href="/manage">Manage Links</a>
        </div>
    </div>
</body>
</html>
"""

def get_db():
    # Don't worry about thread safety, it's local.
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# I spent 3 hours on this regex and still don't fully trust it. 
# Just kidding, no regex here. Simple is better!
def generate_short_code():
    # This might create duplicates once in a blue moon. I'll fix it if I ever share this.
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))



@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        url = request.form.get('url')
        custom_code = request.form.get('custom_code')

        if not url:
            error = "Oops! You forgot the URL."
        else:
            if custom_code:
                # Basic check for alphanumeric
                if not custom_code.isalnum():
                    error = "Custom code must be letters and numbers only."
                else:
                    short_code = custom_code
            else:
                short_code = generate_short_code()

            if not error:
                conn = get_db()
                cur = conn.cursor()
                
                # Check for duplicates
                cur.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
                if cur.fetchone():
                    error = f"Oops! The code '{short_code}' already exists. Try another."
                else:
                    cur.execute('INSERT INTO urls (short_code, original_url) VALUES (?, ?)', (short_code, url))
                    conn.commit()
                    
                    short_url = request.host_url + short_code
                    qr_url = request.host_url + 'qr/' + short_code
                    stats_url = request.host_url + 'stats/' + short_code
                    
                    content = f"""
                        <h2 class='success'>Link Shortened!</h2>
                        <p>Your short link:</p>
                        <input type='text' value='{short_url}' readonly onclick='this.select()'>
                        <p>QR Code:</p>
                        <img src='{qr_url}' alt='QR Code' width='150'>
                        <p><a href='{stats_url}'>View Analytics</a></p>
                    """
                    return render_template_string(LAYOUT_TEMPLATE, content=content)
    
    # Form display
    form_html = f"""
        <p>Shorten a long URL below:</p>
        <form method="POST">
            {f"<div class='error'>{error}</div>" if error else ""}
            <input type="url" name="url" placeholder="https://example.com/very/long/path" required><br>
            <input type="text" name="custom_code" placeholder="Custom code (optional)"><br>
            <button type="submit">Shorten</button>
        </form>
    """
    return render_template_string(LAYOUT_TEMPLATE, content=form_html)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, original_url FROM urls WHERE short_code = ?', (short_code,))
    row = cur.fetchone()
    
    if not row:
        abort(404)
        
    url_id = row['id']
    original_url = row['original_url']
    
    # Track analytics
    ip_address = request.remote_addr
    referrer = request.referrer or "Direct"
    
    # Determine location (gracefully handle local dev)
    country = "Unknown"
    city = "Unknown"
    if ip_address and ip_address != "127.0.0.1":
        try:
            # Simple synchronous call to get geolocation data
            resp = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=2).json()
            if resp.get("status") == "success":
                country = resp.get("country", "Unknown")
                city = resp.get("city", "Unknown")
        except:
            pass # Fail silently, it's just analytics
    else:
        country = "Local Network"
        city = "Local Network"
        
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update stats in two separate queries, like a beginner might do
    cur.execute('UPDATE urls SET clicks = clicks + 1 WHERE id = ?', (url_id,))
    cur.execute('UPDATE urls SET last_accessed = ? WHERE id = ?', (now, url_id))
    
    cur.execute('''
        INSERT INTO clicks (url_id, ip_address, country, city, referrer)
        VALUES (?, ?, ?, ?, ?)
    ''', (url_id, ip_address, country, city, referrer))
    
    db.commit()
    
    return redirect(original_url)

@app.route('/qr/<short_code>')
def generate_qr(short_code):
    import qrcode
    short_url = request.host_url + short_code
    img = qrcode.make(short_url)
    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/stats/<short_code>')
def stats(short_code):
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM urls WHERE short_code = ?', (short_code,))
    url_row = cur.fetchone()
    
    if not url_row:
        abort(404)
        
    # Get click analytics
    cur.execute('SELECT ip_address, country, city, referrer, click_time FROM clicks WHERE url_id = ? ORDER BY click_time DESC LIMIT 10', (url_row['id'],))
    clicks = cur.fetchall()
    
    clicks_html = ""
    for click in clicks:
        clicks_html += f"<tr><td>{click['click_time']}</td><td>{click['country']} / {click['city']}</td><td>{click['referrer']}</td></tr>"
        
    content = f"""
        <h2>Stats for '{short_code}'</h2>
        <p><strong>Original URL:</strong> {url_row['original_url']}</p>
        <p><strong>Total Clicks:</strong> {url_row['clicks']}</p>
        <p><strong>Created At:</strong> {url_row['created_at']}</p>
        <p><strong>Last Accessed:</strong> {url_row['last_accessed'] or 'Never'}</p>
        
        <h3>Recent Clicks (Last 10)</h3>
        <table>
            <tr><th>Time</th><th>Location</th><th>Referrer</th></tr>
            {clicks_html if clicks_html else '<tr><td colspan="3">No clicks yet!</td></tr>'}
        </table>
    """
    return render_template_string(LAYOUT_TEMPLATE, content=content)

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    db = get_db()
    cur = db.cursor()
    
    if request.method == 'POST':
        delete_id = request.form.get('delete_id')
        if delete_id:
            cur.execute('DELETE FROM clicks WHERE url_id = ?', (delete_id,))
            cur.execute('DELETE FROM urls WHERE id = ?', (delete_id,))
            db.commit()
            
    cur.execute('SELECT * FROM urls ORDER BY created_at DESC')
    urls = cur.fetchall()
    
    rows_html = ""
    for u in urls:
        rows_html += f"""
        <tr>
            <td><a href='/{u["short_code"]}' target='_blank'>{u["short_code"]}</a></td>
            <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{u["original_url"]}</td>
            <td>{u["clicks"]}</td>
            <td>
                <a href='/stats/{u["short_code"]}'>Stats</a>
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="delete_id" value="{u["id"]}">
                    <button type="submit" style="padding:2px 5px; background:red;">X</button>
                </form>
            </td>
        </tr>
        """
        
    content = f"""
        <h2>Link Management</h2>
        <table>
            <tr><th>Short Code</th><th>Original URL</th><th>Clicks</th><th>Actions</th></tr>
            {rows_html if rows_html else "<tr><td colspan='4'>No links found.</td></tr>"}
        </table>
    """
    return render_template_string(LAYOUT_TEMPLATE, content=content)

@app.errorhandler(404)
def page_not_found(e):
    content = """
        <h2>404 - Not Found</h2>
        <p>Oops! We couldn't find that page.</p>
        <p>😢</p>
    """
    return render_template_string(LAYOUT_TEMPLATE, content=content), 404

with app.app_context():
    if not os.path.exists(DATABASE):
        init_db()

print("Running on http://localhost:5000")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        # run a simple terminal interface
        from cutlist_cli import main
        main()
    else:
        app.run(debug=True)

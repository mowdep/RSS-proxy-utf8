import os
from flask import Flask, Response, request, render_template_string, redirect, url_for
import requests
import charset_normalizer
import sqlite3

app = Flask(__name__)

# Define the data folder and database path
DATA_FOLDER = './data'
DB_PATH = os.path.join(DATA_FOLDER, 'proxified_urls.db')

# HTML template for the Web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RSS Proxy</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 2rem; }
        form { margin-bottom: 2rem; }
        .proxified-list { margin-top: 2rem; }
    </style>
</head>
<body>
    <h1>RSS Proxy</h1>
    <form method="post" action="/add_url">
        <label for="rss_url">Enter RSS Feed URL:</label><br>
        <input type="url" id="rss_url" name="rss_url" required style="width: 60%; padding: 0.5rem;"><br><br>
        <button type="submit" style="padding: 0.5rem 1rem;">Proxify</button>
    </form>
    <div class="proxified-list">
        <h2>Previous Links Proxified</h2>
        <ul>
            {% for url, encoding in proxified_urls %}
                <li>
                    <a href="{{ url }}" target="_blank">{{ url }}</a> 
                    (Encoding: {{ encoding }})
                </li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
"""

# Initialize the database and data folder
def init_db():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)  # Create the data folder if it doesn't exist

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proxified_url TEXT NOT NULL,
            encoding TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Fetch all proxified URLs and their encodings from the database
def get_all_urls():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT proxified_url, encoding FROM urls')
    urls = cursor.fetchall()
    conn.close()
    return urls

# Add a proxified URL and its encoding to the database
def add_url_to_db(proxified_url, encoding):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO urls (proxified_url, encoding) VALUES (?, ?)', (proxified_url, encoding))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    proxified_urls = get_all_urls()
    return render_template_string(HTML_TEMPLATE, proxified_urls=proxified_urls)

@app.route('/add_url', methods=['POST'])
def add_url():
    rss_url = request.form.get('rss_url')
    if not rss_url:
        return "Missing RSS URL", 400

    # Detect the encoding of the RSS feed
    try:
        response = requests.get(rss_url)
        detected = charset_normalizer.detect(response.content)
        encoding = detected['encoding'] or 'utf-8'
    except Exception as e:
        encoding = "Error detecting encoding"

    # Generate the proxified URL
    proxified_url = f"{request.url_root}proxy?url={rss_url}"

    # Add the proxified URL and its encoding to the database
    add_url_to_db(proxified_url, encoding)

    # Redirect back to the main page
    return redirect(url_for('index'))

@app.route('/proxy')
def rss_proxy():
    # Extract the target RSS feed URL from the query parameter
    target_url = request.args.get('url')
    if not target_url:
        return "Missing 'url' parameter", 400

    try:
        # Extract all other query parameters
        query_params = request.args.to_dict()
        query_params.pop('url', None)  # Remove 'url' from parameters passed to the target

        # Fetch the RSS feed
        response = requests.get(target_url, params=query_params)
        response.encoding = 'windows-1251'  # Decode as Windows-1251

        # Modify the XML declaration to specify UTF-8
        utf8_content = response.text.replace(
            'encoding="windows-1251"', 'encoding="utf-8"'
        ).encode('utf-8')  # Re-encode the content as UTF-8

        # Return the modified content with appropriate headers
        return Response(utf8_content, content_type='application/rss+xml; charset=utf-8')
    except Exception as e:
        return f"Error processing feed: {e}", 500

if __name__ == '__main__':
    init_db()  # Initialize the database and ensure the folder exists
    app.run(host='0.0.0.0', port=8080)

from flask import Flask, request, redirect, url_for, render_template, Response
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)

# ---------------- ADMIN LOGIN ----------------
ADMIN_USER = "admin"
ADMIN_PASS = "anand123"

# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect("enquiries.db")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            message TEXT
        )
    """)
    return conn

def send_email_alert(name, phone, message):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    print("EMAIL_USER:", sender)
    print("EMAIL_PASS exists:", bool(password))

    if not sender or not password:
        print("❌ EMAIL ENV VARIABLES NOT FOUND")
        return

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = sender
    msg["Subject"] = "New Enquiry - Anand Construction"

    body = f"""
New enquiry received:

Name: {name}
Phone: {phone}
Message: {message}
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        print("⏳ Connecting to SMTP...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(1)   # 🔥 THIS IS IMPORTANT
        server.starttls()
        print("🔐 Logging in...")
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ EMAIL ERROR:", repr(e))



# ---------------- BASIC AUTH ----------------
def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS

def authenticate():
    return Response(
        "Login required", 401,
        {"WWW-Authenticate": 'Basic realm="Admin Area"'}
    )

def requires_auth(f):
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ---------------- HOME (WEBSITE) ----------------
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/works")
def works():
    return render_template("works.html")

# ---------------- FORM SUBMIT ----------------
@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    phone = request.form.get("phone")
    message = request.form.get("message")

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO enquiries (name, phone, message) VALUES (?, ?, ?)",
        (name, phone, message)
    )
    conn.commit()
    conn.close()
    send_email_alert(name, phone, message)

    return redirect(url_for("success"))

# ---------------- SUCCESS PAGE ----------------
@app.route("/success")
def success():
    return render_template("success.html")

# ---------------- ADMIN PAGE ----------------
@app.route("/admin")
@requires_auth
def admin():
    conn = get_db_connection()
    enquiries = conn.execute("SELECT * FROM enquiries").fetchall()
    conn.close()

    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Admin Dashboard | Anand Construction</title>
      <link rel="stylesheet" href="/static/style.css">
      <style>
        .admin-container {
          max-width: 1100px;
          margin: 60px auto;
        }
        table {
          width: 100%;
          border-collapse: collapse;
          background: white;
        }
        th, td {
          padding: 14px;
          border-bottom: 1px solid #e5e7eb;
          text-align: left;
        }
        th {
          background: #111827;
          color: #e5e7eb;
        }
        tr:hover {
          background: #f9fafb;
        }
      </style>
    </head>
    <body>

      <div class="admin-container">
        <h2>Client Enquiries</h2>
        <table>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Phone</th>
            <th>Message</th>
          </tr>
    """ + "".join(
        f"""
          <tr>
            <td>{e['id']}</td>
            <td>{e['name']}</td>
            <td>{e['phone']}</td>
            <td>{e['message']}</td>
          </tr>
        """ for e in enquiries
    ) + """
        </table>
      </div>

    </body>
    </html>
    """


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


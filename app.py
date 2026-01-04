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
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

    return conn


# ---------------- EMAIL ALERT ----------------
def send_email_alert(name, phone, message):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    if not sender or not password:
        print("⚠️ Email skipped (env vars not set)")
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
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent")

    except Exception as e:
        # IMPORTANT: never crash app
        print("❌ Email failed:", e)


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


# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/works")
def works():
    return render_template("works.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name")
    phone = request.form.get("phone")
    message = request.form.get("message")

    # Save enquiry (always)
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO enquiries (name, phone, message) VALUES (?, ?, ?)",
        (name, phone, message)
    )
    conn.commit()
    conn.close()

    # Email is OPTIONAL
    try:
        send_email_alert(name, phone, message)
    except Exception as e:
        print("Email exception ignored:", e)

    return redirect(url_for("success"))


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/admin")
@requires_auth
def admin():
    conn = get_db_connection()
    enquiries = conn.execute(
    "SELECT * FROM enquiries ORDER BY id DESC"
).fetchall()

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
            <th>Time</th>
          </tr>
    """ + "".join(
        f"""
          <tr>
            <td>{e['id']}</td>
            <td>{e['name']}</td>
            <td>{e['phone']}</td>
            <td>{e['message']}</td>
            <td>{e['created_at']}</td>

          </tr>
        """ for e in enquiries
    ) + """
        </table>
      </div>
    </body>
    </html>
    """


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

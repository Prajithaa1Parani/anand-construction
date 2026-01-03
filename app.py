from flask import Flask, request, redirect, url_for, render_template, Response
import sqlite3

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


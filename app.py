from flask import Flask, redirect, url_for, session, request, render_template
import pathlib
import os
import requests
import dotenv
from datetime import datetime
import pytz

from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

dotenv.load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="http://127.0.0.1:5000/callback",
)


def print_design(n):
    base = "FORMULAQSOLUTIONS"
    extended = base * 5 
    lines = []
    
    if n % 2 == 1:
        
        middle = (n + 1) // 2
        max_length = 2 * middle - 1
        total_lines = n
        
        for i in range(1, total_lines + 1):
            if i <= middle:
                length = 2 * i - 1
            else:
                length = 2 * (n - i) + 1
            
            start_pos = i - 1
            substring = extended[start_pos:start_pos + length]
            
            
            spaces = " " * ((max_length - length) // 2)
            lines.append(spaces + substring)
    else:
        
        peak_line = n // 2 + 1
        max_length = 2 * peak_line - 1
        total_lines = n + 1  
        
        for i in range(1, total_lines + 1):
            if i <= peak_line:
                length = 2 * i - 1
            else:
                length = 2 * (total_lines - i) + 1
            
            start_pos = i - 1
            substring = extended[start_pos:start_pos + length]
            
            spaces = " " * ((max_length - length) // 2)
            lines.append(spaces + substring)
    
    return lines

def generate_pattern_response(n):
    try:
        n = int(n)
        n = max(1, min(100, n))  
        
        lines = print_design(n)
        pattern = '\n'.join(lines)
        
        return {
            'success': True,
            'input': n,
            'pattern': pattern,
            'total_lines': len(lines)
        }
    except (ValueError, TypeError):
        return {
            'success': False,
            'error': 'Please enter a valid integer between 1 and 100.'
        }


@app.route("/")
def home():
    if "google_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "google_id" not in session:
        return redirect(url_for("home"))

    # Current IST
    ist = pytz.timezone("Asia/Kolkata")
    current_time = datetime.now(ist).strftime("%A, %d %B %Y %I:%M %p")

    design_output = None
    num_lines = None

    if request.method == "POST":
        num_lines_input = request.form.get("num_lines")
        
        response = generate_pattern_response(num_lines_input)
        
        if response['success']:
            design_output = response['pattern']
            num_lines = response['input']
        else:
            design_output = response['error']

    return render_template(
        "index.html",
        name=session["name"],
        email=session["email"],
        picture=session["picture"],
        current_time=current_time,
        design_output=design_output,
        num_lines=num_lines,
    )


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        return redirect(url_for("home"))

    credentials = flow.credentials
    request_session = requests.session()
    token_request = google.auth.transport.requests.Request(session=request_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token, request=token_request, audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session["picture"] = id_info.get("picture")

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

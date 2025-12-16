from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from bson.objectid import ObjectId
from app import app, db, bcrypt, Professor
import random
import smtplib
from email.mime.text import MIMEText
import config


# ---------- HELPER: SEND OTP EMAIL ----------

# def send_otp_email(to_email, otp_code):
#     msg = MIMEText(f"Your verification OTP is: {otp_code}")
#     msg["Subject"] = "Professor Signup Verification OTP"
#     msg["From"] = config.SMTP_USER
#     msg["To"] = to_email

#     with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
#         server.starttls()
#         server.login(config.SMTP_USER, config.SMTP_PASSWORD)
#         server.send_message(msg)

def send_otp_email(email, otp_code):
    # Render demo: log OTP instead of sending email (SMTP often blocked)
    print("OTP for", email, "is", otp_code)


# ---------- ROUTES ----------

@app.route("/")
def home():
    return render_template("home.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("All fields are required", "danger")
            return redirect(url_for("signup"))

        existing = db.professors.find_one({"email": email})
        if existing:
            flash("Email already registered", "danger")
            return redirect(url_for("signup"))

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

        # ----- NEW: generate OTP, store is_verified + otp -----
        otp_code = str(random.randint(100000, 999999))

        db.professors.insert_one({
            "name": name,
            "email": email,
            "password": pw_hash,
            "is_verified": False,
            "otp": otp_code
        })

        # send OTP email
        send_otp_email(email, otp_code)

        flash("Account created. OTP sent to your email, please verify.", "info")
        return redirect(url_for("verify_otp", email=email))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        prof_doc = db.professors.find_one({"email": email})
        if prof_doc and bcrypt.check_password_hash(prof_doc["password"], password):

            # ----- NEW: block login if not verified -----
            if not prof_doc.get("is_verified", False):
                flash("Please verify your email with OTP before logging in.", "warning")
                return redirect(url_for("verify_otp", email=prof_doc["email"]))

            login_user(Professor(prof_doc))
            return redirect(url_for("dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    students = list(db.students.find({"professor_id": current_user.id}))
    return render_template("dashboard.html", name=current_user.name, students=students)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ---------- NEW: VERIFY OTP ROUTE ----------

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = request.args.get("email") or request.form.get("email")
    if not email:
        flash("Email missing for OTP verification.", "danger")
        return redirect(url_for("signup"))

    if request.method == "POST":
        otp_input = request.form.get("otp")
        prof = db.professors.find_one({"email": email})
        if prof and prof.get("otp") == otp_input:
            db.professors.update_one(
                {"email": email},
                {"$set": {"is_verified": True}, "$unset": {"otp": ""}}
            )
            flash("Email verified. You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template("verify_otp.html", email=email)

@app.route("/resend-otp")
def resend_otp():
    email = request.args.get("email")
    if not email:
        flash("Email missing for OTP resend.", "danger")
        return redirect(url_for("signup"))

    prof = db.professors.find_one({"email": email})
    if not prof:
        flash("Account not found for this email.", "danger")
        return redirect(url_for("signup"))

    if prof.get("is_verified", False):
        flash("This account is already verified. Please log in.", "info")
        return redirect(url_for("login"))

    # generate a new OTP
    otp_code = str(random.randint(100000, 999999))

    db.professors.update_one(
        {"email": email},
        {"$set": {"otp": otp_code}}
    )

    send_otp_email(email, otp_code)
    flash("A new OTP has been sent to your email.", "info")
    return redirect(url_for("verify_otp", email=email))

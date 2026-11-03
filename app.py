import os
from dotenv import load_dotenv
from datetime import datetime
from functools import wraps

load_dotenv(override=True)
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-before-deploying")
db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/javas_restaurant")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"), nullable=False)
    meal_type = db.Column(db.String(80), nullable=False)
    package_days = db.Column(db.Integer, nullable=False, default=30)
    meals_included = db.Column(db.String(120), nullable=False, default="Breakfast, Lunch, Dinner")
    diet_notes = db.Column(db.Text)
    hospital = db.Column(db.String(180), nullable=False)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_date = db.Column(db.String(20), nullable=False)
    delivery_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship("Customer", backref="bookings")

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("booking.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(40), default="Cash")
    status = db.Column(db.String(30), default="Pending")
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "customer_id" not in session:
            flash("Fadlan marka hore gal akoonkaaga.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Boggan waxaa geli kara maamulka oo keliya.", "error")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def send_whatsapp(to_number, message):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    if not token or not phone_id or not to_number:
        app.logger.info("WhatsApp not configured; skipped notification.")
        return False
    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    payload = {"messaging_product": "whatsapp", "to": to_number,
               "type": "text", "text": {"body": message}}
    try:
        response = requests.post(url, json=payload,
            headers={"Authorization": f"Bearer {token}"}, timeout=15)
        response.raise_for_status()
        return True
    except requests.RequestException as exc:
        app.logger.exception("WhatsApp send failed: %s", exc)
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name","").strip(), request.form.get("email","").strip().lower()
        phone, password = request.form.get("phone","").strip(), request.form.get("password","")
        if not all([name, email, phone, password]) or len(password) < 8:
            flash("Buuxi dhammaan meelaha; furaha sirta ahi ha ahaado ugu yaraan 8 xaraf.", "error")
        elif Customer.query.filter_by(email=email).first():
            flash("Email-kan horay ayaa loo diiwaangeliyey.", "error")
        else:
            customer = Customer(name=name, email=email, phone=phone,
                                password_hash=generate_password_hash(password))
            db.session.add(customer); db.session.commit()
            session["customer_id"] = customer.id
            flash("Akoonkaaga waa la sameeyey.", "success")
            return redirect(url_for("booking"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if email == os.getenv("ADMIN_EMAIL") and password == os.getenv("ADMIN_PASSWORD") and email:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        customer = Customer.query.filter_by(email=email).first()
        if customer and check_password_hash(customer.password_hash, password):
            session["customer_id"] = customer.id
            return redirect(url_for("customer_dashboard"))
        flash("Email ama password khaldan.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/booking", methods=["GET", "POST"])
@login_required
def booking():
    if request.method == "POST":
        customer = db.session.get(Customer, session["customer_id"])
        item = Booking(customer_id=customer.id,
            meal_type=request.form.get("meal_type",""),
            package_days=30,
            meals_included="Breakfast, Lunch, Dinner",
            diet_notes=request.form.get("diet_notes",""),
            hospital=request.form.get("hospital",""),
            delivery_address=request.form.get("delivery_address",""),
            delivery_date=request.form.get("delivery_date",""),
            delivery_time=request.form.get("delivery_time",""))
        required = [item.meal_type, item.hospital, item.delivery_address, item.delivery_date, item.delivery_time]
        if not all(required):
            flash("Fadlan buuxi dhammaan meelaha muhiimka ah.", "error")
        else:
            db.session.add(item); db.session.commit()
            send_whatsapp(customer.phone, f"JAVA'S RESTAURANT: Booking-kaaga #{item.id} ee 30 maalmood (quraac, qado iyo casho) waa la helay. Qiimaha waxaan kaala heshiin doonnaa telefoon. Xaalad: Pending.")
            admin_phone = os.getenv("ADMIN_WHATSAPP_NUMBER")
            send_whatsapp(admin_phone, f"Booking cusub #{item.id}: {customer.name}, {customer.phone}, {item.hospital}. Xirmo 30 maalmood: quraac, qado iyo casho. Fadlan telefoon kula heshiis qiimaha.")
            flash("Booking-ka waa la diray. Mahadsanid!", "success")
            return redirect(url_for("customer_dashboard"))
    return render_template("booking.html")

@app.route("/account")
@login_required
def customer_dashboard():
    customer = db.session.get(Customer, session["customer_id"])
    return render_template("account.html", customer=customer,
                           bookings=Booking.query.filter_by(customer_id=customer.id).order_by(Booking.created_at.desc()).all())

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html",
        customers=Customer.query.order_by(Customer.created_at.desc()).all(),
        bookings=Booking.query.order_by(Booking.created_at.desc()).all(),
        payments=Payment.query.order_by(Payment.created_at.desc()).all())

@app.route("/admin/booking/<int:booking_id>/status", methods=["POST"])
@admin_required
def update_booking(booking_id):
    item = db.session.get(Booking, booking_id)
    if not item: return jsonify({"error":"Booking not found"}), 404
    status = request.form.get("status")
    if status not in ["Pending", "Confirmed", "Preparing", "Delivered", "Cancelled"]:
        return jsonify({"error":"Invalid status"}), 400
    item.status = status; db.session.commit()
    send_whatsapp(item.customer.phone, f"JAVA'S RESTAURANT: Xaaladda booking-kaaga #{item.id} waa {status}.")
    flash("Xaaladda booking-ka waa la cusboonaysiiyey.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/payment", methods=["POST"])
@admin_required
def add_payment():
    booking_id = request.form.get("booking_id", type=int)
    amount = request.form.get("amount", type=float)
    item = db.session.get(Booking, booking_id) if booking_id else None
    if not item or not amount or amount <= 0:
        flash("Hubi booking ID iyo lacagta.", "error")
    else:
        db.session.add(Payment(booking_id=booking_id, amount=amount,
            method=request.form.get("method","Cash"), status=request.form.get("status","Paid"),
            reference=request.form.get("reference","")))
        db.session.commit()
        flash("Payment record waa la kaydiyey.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/health")
def health():
    return jsonify({"status":"ok", "app":"Java's Restaurant"})

@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database tables created.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")

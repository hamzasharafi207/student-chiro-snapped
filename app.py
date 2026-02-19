import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Config ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "chiro.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# --- Model ---
class Chiropractor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    clinic_name = db.Column(db.String(120), nullable=False)
    sports_focus = db.Column(db.String(200), nullable=False)  # comma-separated
    student_friendly = db.Column(db.Boolean, default=False)
    evening_hours = db.Column(db.Boolean, default=False)
    price_range = db.Column(db.String(50), nullable=True)  # e.g. "$$ (60–80)"
    bio = db.Column(db.Text, nullable=True)


def init_db_if_needed():
    """Create and seed the database if it doesn't exist."""
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()

            demo_chiros = [
                Chiropractor(
                    name="Dr. Alex Chen",
                    city="London, ON",
                    clinic_name="Campus Sports Chiro",
                    sports_focus="soccer, weightlifting, running",
                    student_friendly=True,
                    evening_hours=True,
                    price_range="$$ (60–80)",
                    bio="Focus on lower-body injuries, return-to-play for field sports, and lifters with back pain."
                ),
                Chiropractor(
                    name="Dr. Maya Singh",
                    city="Toronto, ON",
                    clinic_name="Downtown Performance Chiro",
                    sports_focus="basketball, volleyball, running",
                    student_friendly=False,
                    evening_hours=True,
                    price_range="$$$ (80–110)",
                    bio="Works with varsity athletes. Emphasis on shoulder/knee mechanics."
                ),
                Chiropractor(
                    name="Dr. Jacob Rivera",
                    city="London, ON",
                    clinic_name="Flexline Student Chiro",
                    sports_focus="weightlifting, powerlifting",
                    student_friendly=True,
                    evening_hours=False,
                    price_range="$ (40–60)",
                    bio="Budget-friendly care tailored to student lifters."
                ),
            ]

            db.session.add_all(demo_chiros)
            db.session.commit()
            print("Database created and demo chiropractors added.")


# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/chiropractors")
def list_chiropractors():
    # Read filters from the URL ?city=...&sport=... etc.
    city = request.args.get("city", "").strip()
    sport = request.args.get("sport", "").strip().lower()
    student_only = request.args.get("student_only") == "on"
    evenings_only = request.args.get("evenings_only") == "on"

    query = Chiropractor.query

    if city:
        query = query.filter(Chiropractor.city.ilike(f"%{city}%"))

    if sport:
        query = query.filter(Chiropractor.sports_focus.ilike(f"%{sport}%"))

    if student_only:
        query = query.filter_by(student_friendly=True)

    if evenings_only:
        query = query.filter_by(evening_hours=True)

    chiros = query.all()

    return render_template(
        "chiropractors.html",
        chiropractors=chiros,
        filters={
            "city": city,
            "sport": sport,
            "student_only": student_only,
            "evenings_only": evenings_only,
        },
    )


@app.route("/chiropractors/<int:chiro_id>")
def chiro_profile(chiro_id):
    chiro = Chiropractor.query.get_or_404(chiro_id)
    sports_list = [s.strip() for s in chiro.sports_focus.split(",") if s.strip()]
    return render_template("profile.html", chiro=chiro, sports_list=sports_list)


@app.route("/submit", methods=["GET", "POST"])
def submit_chiropractor():
    if request.method == "POST":
        form = request.form

        new_chiro = Chiropractor(
            name=form.get("name") or "",
            clinic_name=form.get("clinic_name") or "",
            city=form.get("city") or "",
            sports_focus=form.get("sports_focus") or "",
            student_friendly=("student_friendly" in form),
            evening_hours=("evening_hours" in form),
            price_range=form.get("price_range") or "",
            bio=form.get("bio") or "",
        )

        db.session.add(new_chiro)
        db.session.commit()

        return render_template("submit_success.html", chiro=new_chiro)

    return render_template("submit.html")


if __name__ == "__main__":
    init_db_if_needed()
    # Using port 5001 so nothing else interferes
    app.run(debug=True, host="127.0.0.1", port=5001)

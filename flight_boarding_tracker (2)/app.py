import os
import sqlite3
import time
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import Flask, flash, g, jsonify, redirect, render_template, request, url_for

from algorithms.searching import binary_search, linear_search
from algorithms.sorting import SORTERS, quick_sort

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "college-project-secret")
DATABASE = os.path.join(os.path.dirname(__file__), "database.db")

STATUSES = ["Scheduled", "Boarding", "Departed", "Delayed", "Cancelled", "Arrived"]
PASSENGER_TYPES = ["Normal", "Senior Citizen", "Child", "Special Assistance"]
BOARDING_STATUSES = ["Waiting", "Boarded", "Not Boarded"]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number TEXT NOT NULL UNIQUE,
        airline TEXT NOT NULL,
        source TEXT NOT NULL,
        destination TEXT NOT NULL,
        departure TEXT NOT NULL,
        arrival TEXT NOT NULL,
        gate TEXT,
        terminal TEXT,
        status TEXT NOT NULL DEFAULT 'Scheduled'
    );
    CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        flight_number TEXT NOT NULL,
        seat_number TEXT NOT NULL,
        boarding_group INTEGER NOT NULL DEFAULT 5,
        priority INTEGER NOT NULL DEFAULT 5,
        passenger_type TEXT NOT NULL DEFAULT 'Normal',
        boarding_status TEXT NOT NULL DEFAULT 'Waiting'
    );
    """)
    count = db.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    if count == 0:
        flights = [
            ("AI-101", "Air India", "DEL", "BOM", "2026-09-29 16:30", "2026-09-29 18:40", "A12", "T3", "Boarding"),
            ("6E-245", "IndiGo", "AMD", "DEL", "2026-09-29 18:10", "2026-09-29 19:45", "B04", "T1", "Scheduled"),
            ("UK-955", "Vistara", "BOM", "BLR", "2026-09-29 20:00", "2026-09-29 21:45", "C08", "T2", "Delayed"),
            ("SG-402", "SpiceJet", "DEL", "GOI", "2026-09-29 21:20", "2026-09-29 23:50", "D03", "T1", "Scheduled"),
        ]
        db.executemany("""INSERT INTO flights
            (flight_number, airline, source, destination, departure, arrival, gate, terminal, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", flights)
    pcount = db.execute("SELECT COUNT(*) FROM passengers").fetchone()[0]
    if pcount == 0:
        passengers = [
            (1001, "Aarav Shah", "AI-101", "12A", 1, 1, "Senior Citizen", "Boarded"),
            (1002, "Riya Patel", "AI-101", "12B", 2, 2, "Normal", "Boarded"),
            (1003, "Kabir Mehta", "AI-101", "14C", 3, 3, "Normal", "Waiting"),
            (1004, "Anaya Desai", "AI-101", "15D", 5, 5, "Normal", "Waiting"),
            (1005, "Vivaan Joshi", "6E-245", "7A", 2, 2, "Normal", "Waiting"),
            (1006, "Ishita Rao", "6E-245", "7B", 1, 1, "Special Assistance", "Waiting"),
            (1007, "Arjun Singh", "UK-955", "20F", 5, 5, "Normal", "Not Boarded"),
            (1008, "Myra Kapoor", "UK-955", "21A", 4, 4, "Child", "Waiting"),
            (1009, "Dev Malhotra", "SG-402", "8C", 3, 3, "Normal", "Waiting"),
            (1010, "Sara Khan", "SG-402", "8D", 1, 1, "Senior Citizen", "Boarded"),
        ]
        db.executemany("""INSERT INTO passengers
            (passenger_id, name, flight_number, seat_number, boarding_group, priority, passenger_type, boarding_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", passengers)
    db.commit()
    db.close()


def safe_form(form):
    return {key: form.get(key, "").strip() for key in form.keys()}


@app.context_processor
def inject_choices():
    return {"flight_statuses": STATUSES, "passenger_types": PASSENGER_TYPES,
            "boarding_statuses": BOARDING_STATUSES}


@app.route("/")
def dashboard():
    flights = query_db("SELECT * FROM flights ORDER BY departure LIMIT 8")
    stats = {
        "flights": query_db("SELECT COUNT(*) AS c FROM flights", one=True)["c"],
        "passengers": query_db("SELECT COUNT(*) AS c FROM passengers", one=True)["c"],
        "boarded": query_db("SELECT COUNT(*) AS c FROM passengers WHERE boarding_status='Boarded'", one=True)["c"],
        "waiting": query_db("SELECT COUNT(*) AS c FROM passengers WHERE boarding_status='Waiting'", one=True)["c"],
        "active": query_db("SELECT COUNT(*) AS c FROM flights WHERE status IN ('Boarding','Departed')", one=True)["c"],
        "delayed": query_db("SELECT COUNT(*) AS c FROM flights WHERE status='Delayed'", one=True)["c"],
    }
    not_boarded = stats["passengers"] - stats["boarded"] - stats["waiting"]
    return render_template("index.html", flights=flights, stats=stats, not_boarded=max(0, not_boarded))


@app.route("/flights", methods=["GET", "POST"])
def flights_page():
    if request.method == "POST":
        f = safe_form(request.form)
        required = ["flight_number", "airline", "source", "destination", "departure", "arrival", "status"]
        if any(not f.get(x) for x in required):
            flash("Please fill all required flight fields.", "error")
        else:
            try:
                db = get_db()
                db.execute("""INSERT INTO flights
                    (flight_number, airline, source, destination, departure, arrival, gate, terminal, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f["flight_number"].upper(), f["airline"], f["source"].upper(), f["destination"].upper(),
                     f["departure"], f["arrival"], f.get("gate", ""), f.get("terminal", ""), f["status"]))
                db.commit()
                flash("Flight added successfully.", "success")
            except sqlite3.IntegrityError:
                flash("Flight number already exists.", "error")
            return redirect(url_for("flights_page"))
    flights = query_db("SELECT * FROM flights ORDER BY departure")
    return render_template("flights.html", flights=flights)


@app.route("/flights/<int:flight_id>/edit", methods=["GET", "POST"])
def edit_flight(flight_id):
    flight = query_db("SELECT * FROM flights WHERE id=?", (flight_id,), one=True)
    if not flight:
        flash("Flight not found.", "error"); return redirect(url_for("flights_page"))
    if request.method == "POST":
        f = safe_form(request.form)
        try:
            get_db().execute("""UPDATE flights SET flight_number=?, airline=?, source=?, destination=?, departure=?, arrival=?, gate=?, terminal=?, status=? WHERE id=?""",
                             (f["flight_number"].upper(), f["airline"], f["source"].upper(), f["destination"].upper(), f["departure"], f["arrival"], f.get("gate", ""), f.get("terminal", ""), f["status"], flight_id))
            get_db().commit(); flash("Flight updated.", "success")
        except sqlite3.IntegrityError:
            flash("Another flight already uses that flight number.", "error")
        return redirect(url_for("flights_page"))
    return render_template("edit_flight.html", flight=flight)


@app.post("/flights/<int:flight_id>/delete")
def delete_flight(flight_id):
    try:
        db = get_db(); db.execute("DELETE FROM flights WHERE id=?", (flight_id,)); db.commit()
        flash("Flight deleted.", "success")
    except sqlite3.Error:
        flash("Database error while deleting flight.", "error")
    return redirect(url_for("flights_page"))


@app.route("/passengers", methods=["GET", "POST"])
def passengers_page():
    if request.method == "POST":
        p = safe_form(request.form)
        required = ["passenger_id", "name", "flight_number", "seat_number", "boarding_group", "priority", "passenger_type", "boarding_status"]
        if any(not p.get(x) for x in required):
            flash("Please fill all passenger fields.", "error")
        else:
            try:
                pid = int(p["passenger_id"]); group = int(p["boarding_group"]); priority = int(p["priority"])
                if pid <= 0 or not 1 <= group <= 5 or not 1 <= priority <= 5:
                    raise ValueError
                flight = query_db("SELECT 1 FROM flights WHERE flight_number=?", (p["flight_number"].upper(),), one=True)
                if not flight:
                    flash("Flight number does not exist.", "error")
                else:
                    db = get_db(); db.execute("""INSERT INTO passengers
                        (passenger_id,name,flight_number,seat_number,boarding_group,priority,passenger_type,boarding_status)
                        VALUES (?,?,?,?,?,?,?,?)""", (pid,p["name"],p["flight_number"].upper(),p["seat_number"].upper(),group,priority,p["passenger_type"],p["boarding_status"]))
                    db.commit(); flash("Passenger added successfully.", "success")
            except ValueError:
                flash("Passenger ID, group and priority must be valid numbers. Group/priority must be 1-5.", "error")
            except sqlite3.IntegrityError:
                flash("Passenger ID already exists.", "error")
            return redirect(url_for("passengers_page"))
    passengers = query_db("SELECT * FROM passengers ORDER BY id")
    flights = query_db("SELECT flight_number FROM flights ORDER BY flight_number")
    return render_template("passengers.html", passengers=passengers, flights=flights)


@app.route("/passengers/<int:row_id>/edit", methods=["GET", "POST"])
def edit_passenger(row_id):
    passenger = query_db("SELECT * FROM passengers WHERE id=?", (row_id,), one=True)
    if not passenger:
        flash("Passenger not found.", "error"); return redirect(url_for("passengers_page"))
    if request.method == "POST":
        p = safe_form(request.form)
        try:
            db = get_db(); db.execute("""UPDATE passengers SET passenger_id=?,name=?,flight_number=?,seat_number=?,boarding_group=?,priority=?,passenger_type=?,boarding_status=? WHERE id=?""",
                (int(p["passenger_id"]), p["name"], p["flight_number"].upper(), p["seat_number"].upper(), int(p["boarding_group"]), int(p["priority"]), p["passenger_type"], p["boarding_status"], row_id))
            db.commit(); flash("Passenger updated.", "success")
        except (ValueError, sqlite3.IntegrityError):
            flash("Invalid values or duplicate passenger ID.", "error")
        return redirect(url_for("passengers_page"))
    flights = query_db("SELECT flight_number FROM flights ORDER BY flight_number")
    return render_template("edit_passenger.html", passenger=passenger, flights=flights)


@app.post("/passengers/<int:row_id>/delete")
def delete_passenger(row_id):
    get_db().execute("DELETE FROM passengers WHERE id=?", (row_id,)); get_db().commit()
    flash("Passenger deleted.", "success")
    return redirect(url_for("passengers_page"))


@app.route("/boarding")
def boarding():
    passengers = query_db("SELECT * FROM passengers ORDER BY priority, passenger_id")
    flight_progress = []
    for flight in query_db("SELECT * FROM flights ORDER BY departure"):
        total = query_db("SELECT COUNT(*) AS c FROM passengers WHERE flight_number=?", (flight["flight_number"],), one=True)["c"]
        boarded = query_db("SELECT COUNT(*) AS c FROM passengers WHERE flight_number=? AND boarding_status='Boarded'", (flight["flight_number"],), one=True)["c"]
        percent = round(boarded / total * 100) if total else 0
        flight_progress.append({"flight": flight, "total": total, "boarded": boarded, "percent": percent})
    return render_template("boarding.html", passengers=passengers, flight_progress=flight_progress)


@app.post("/boarding/<int:row_id>/<action>")
def boarding_action(row_id, action):
    status_map = {"board": "Boarded", "not-boarded": "Not Boarded", "reset": "Waiting"}
    status = status_map.get(action)
    if status:
        get_db().execute("UPDATE passengers SET boarding_status=? WHERE id=?", (status, row_id)); get_db().commit()
        flash(f"Passenger status changed to {status}.", "success")
    return redirect(url_for("boarding"))


@app.route("/sorting")
def sorting_page():
    passengers = [dict(r) for r in query_db("SELECT * FROM passengers ORDER BY id")]
    return render_template("sorting.html", passengers=passengers)


@app.post("/api/quick-sort")
def api_quick_sort():
    data = request.get_json(silent=True) or {}
    records = data.get("records") or [dict(r) for r in query_db("SELECT * FROM passengers ORDER BY id")]
    key = data.get("key", "priority")
    descending = bool(data.get("descending", False))
    if key not in {"name", "passenger_id", "seat_number", "boarding_group", "priority", "flight_number"}:
        return jsonify({"error": "Invalid sort field."}), 400
    result, metrics = quick_sort(records, key, descending)
    return jsonify({"records": result, "metrics": metrics})


@app.post("/api/compare")
def api_compare():
    data = request.get_json(silent=True) or {}
    records = data.get("records") or [dict(r) for r in query_db("SELECT * FROM passengers ORDER BY id")]
    key = data.get("key", "priority")
    if key not in {"name", "passenger_id", "seat_number", "boarding_group", "priority", "flight_number"}:
        return jsonify({"error": "Invalid sort field."}), 400
    results = []
    for name, sorter in SORTERS.items():
        output, metrics = sorter(records, key, False)
        results.append({"algorithm": name, "input_size": len(records), **metrics})
    return jsonify({"results": results})


@app.route("/comparison")
def comparison():
    return render_template("comparison.html")


@app.route("/search", methods=["GET", "POST"])
def search_page():
    query = request.args.get("q", "").strip()
    flight_results = []
    passenger_results = []
    if query:
        like = f"%{query}%"
        flight_results = query_db("""SELECT * FROM flights WHERE flight_number LIKE ? OR airline LIKE ? OR source LIKE ? OR destination LIKE ? ORDER BY departure""", (like,like,like,like))
        passenger_results = query_db("SELECT * FROM passengers WHERE name LIKE ? OR CAST(passenger_id AS TEXT) LIKE ? OR flight_number LIKE ?", (like,like,like))
    return render_template("search.html", query=query, flights=flight_results, passengers=passenger_results)


@app.post("/api/passenger-search")
def api_passenger_search():
    data = request.get_json(silent=True) or {}
    target = str(data.get("passenger_id", "")).strip()
    records = [dict(r) for r in query_db("SELECT * FROM passengers ORDER BY id")]
    linear = linear_search(records, target)
    sorted_records, _ = SORTERS["Quick Sort"](records, "passenger_id", False)
    binary = binary_search(sorted_records, target)
    return jsonify({"linear": linear, "binary": binary, "binary_data_sorted": True})


@app.route("/tracking")
def tracking_page():
    return render_template("tracking.html", api_ready=bool(os.getenv("AVIATIONSTACK_API_KEY")))


@app.get("/api/tracking")
def api_tracking():
    key = os.getenv("AVIATIONSTACK_API_KEY", "").strip()
    if not key or key == "YOUR_API_KEY":
        return jsonify({"ok": False, "message": "Live flight data is currently unavailable. Add AVIATIONSTACK_API_KEY to your .env file."}), 503
    flight_number = request.args.get("flight", "").strip()
    if not flight_number:
        return jsonify({"ok": False, "message": "Please enter a flight number."}), 400
    try:
        response = requests.get("https://api.aviationstack.com/v1/flights", params={"access_key": key, "flight_iata": flight_number}, timeout=10)
        data = response.json()
        if response.status_code != 200 or data.get("error"):
            return jsonify({"ok": False, "message": data.get("error", {}).get("message", "Aviationstack request failed.")}), 502
        flights = data.get("data", [])
        if not flights:
            return jsonify({"ok": False, "message": "No matching flight was returned by Aviationstack."}), 404
        f = flights[0]
        return jsonify({"ok": True, "flight": {
            "flight_number": (f.get("flight") or {}).get("iata") or (f.get("flight") or {}).get("number"),
            "airline": (f.get("airline") or {}).get("name"),
            "departure_airport": (f.get("departure") or {}).get("airport"),
            "arrival_airport": (f.get("arrival") or {}).get("airport"),
            "departure_time": (f.get("departure") or {}).get("estimated") or (f.get("departure") or {}).get("scheduled"),
            "arrival_time": (f.get("arrival") or {}).get("estimated") or (f.get("arrival") or {}).get("scheduled"),
            "status": f.get("flight_status"),
            "departure_terminal": (f.get("departure") or {}).get("terminal"),
            "departure_gate": (f.get("departure") or {}).get("gate"),
            "arrival_terminal": (f.get("arrival") or {}).get("terminal"),
            "arrival_gate": (f.get("arrival") or {}).get("gate"),
            "latitude": (f.get("live") or {}).get("latitude"),
            "longitude": (f.get("live") or {}).get("longitude"),
            "altitude": (f.get("live") or {}).get("altitude"),
            "speed": (f.get("live") or {}).get("speed_horizontal"),
        }})
    except requests.RequestException:
        return jsonify({"ok": False, "message": "Live flight data is currently unavailable. You can still use the local flight management and DAA features."}), 503
    except ValueError:
        return jsonify({"ok": False, "message": "The flight API returned an invalid response."}), 502


@app.route("/about")
def about():
    return render_template("about.html")


@app.errorhandler(500)
def server_error(error):
    return render_template("error.html", message="Something went wrong on the server. Please try again."), 500


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)

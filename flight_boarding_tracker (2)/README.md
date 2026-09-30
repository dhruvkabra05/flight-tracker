# Flight Boarding Tracker & Passenger Sorting System

A 5th-semester B.Tech Information Technology DAA project using Flask, SQLite, HTML/CSS/JavaScript and optional Aviationstack flight data.

## Features

- Dashboard statistics from SQLite
- Flight CRUD
- Passenger CRUD
- Boarding status management and progress
- Priority boarding using a manually implemented Quick Sort
- Quick Sort, Merge Sort, Insertion Sort, Selection Sort and Bubble Sort
- Real measured comparison of the five sorting algorithms
- Linear Search and Binary Search demonstration
- Aviationstack flight lookup through the Flask backend
- Responsive student-project UI

## Folder structure

```text
flight_boarding_tracker/
├── app.py
├── algorithms/
│   ├── sorting.py
│   └── searching.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── flights.html
│   ├── edit_flight.html
│   ├── passengers.html
│   ├── edit_passenger.html
│   ├── boarding.html
│   ├── tracking.html
│   ├── sorting.html
│   ├── comparison.html
│   ├── search.html
│   ├── about.html
│   └── error.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── .env.example
├── requirements.txt
├── README.md
└── database.db   # created automatically on first run
```

## Installation

Python 3.10+ is recommended.

```bash
cd flight_boarding_tracker
python -m venv venv
```

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Aviationstack API key

1. Create an Aviationstack account and obtain an API key.
2. Copy `.env.example` to `.env`.
3. Replace the placeholder value:

```env
AVIATIONSTACK_API_KEY=YOUR_REAL_KEY
```

The key is read only by Flask. It is never put in HTML or browser JavaScript.

If no key is configured, the local flight, passenger, boarding and DAA features still work.

## Run

```bash
python app.py
```

Then open the local address shown by Flask, normally:

```text
http://127.0.0.1:5000
```

## How Quick Sort is applied

Problem: arrange passengers by boarding priority.

Input: passenger records containing priority values.

Processing: the Python Quick Sort implementation chooses a pivot, partitions the records, then recursively sorts the two partitions.

Output: an ordered passenger list plus the number of elements, comparisons, swaps and measured execution time.

Complexity:

- Best: O(n log n)
- Average: O(n log n)
- Worst: O(n²)
- Average recursive stack space: O(log n), worst case O(n)

The DAA algorithms are manually implemented. Python's built-in `sort()` and JavaScript's `.sort()` are not used for the algorithm demonstrations.

## Aviationstack integration

The Flask endpoint `/api/tracking` calls Aviationstack's `/v1/flights` endpoint using the configured access key and a `flight_iata` filter. The frontend only receives returned flight fields. API failures are handled without stopping the rest of the website.



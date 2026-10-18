
from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
import mysql.connector
from mysql.connector import Error, IntegrityError
import os
import uuid
import time

app = Flask(__name__)
CORS(app)

# Prometheus metrics
metrics = PrometheusMetrics(app)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "ridebooking")
DB_USER = os.getenv("DB_USER", "rideuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ridepassword")


def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connection_timeout=5
    )


def init_db():
    """Create required tables after connecting to MySQL."""
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(150) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rides (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ride_id VARCHAR(50) UNIQUE NOT NULL,
                user_id INT NOT NULL,
                pickup VARCHAR(255) NOT NULL,
                destination VARCHAR(255) NOT NULL,
                ride_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) DEFAULT 'BOOKED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_ride_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
        """)

        connection.commit()
        print("Database tables initialized successfully.")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def connect_with_retry(attempts=10, delay=3):
    """Retry database initialization while MySQL starts."""
    for attempt in range(1, attempts + 1):
        try:
            init_db()
            return True
        except Error as error:
            print(
                f"MySQL connection attempt {attempt}/{attempts} failed: "
                f"{error}"
            )

            if attempt < attempts:
                time.sleep(delay)

    print("Database initialization failed. Check DB_HOST and MySQL.")
    return False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "ride-booking-backend"
    }), 200


@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON body is required"}), 400

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not email:
        return jsonify({"error": "Email is required"}), 400
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO users (name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (name, email, phone, password))

        connection.commit()
        user_id = cursor.lastrowid

        return jsonify({
            "message": "User registered successfully",
            "user": {
                "user_id": user_id,
                "name": name,
                "email": email,
                "phone": phone
            }
        }), 201

    except IntegrityError:
        if connection and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Email or phone number already exists"
        }), 409

    except Error:
        app.logger.exception("Database error while registering user")

        if connection and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Unable to register user due to a database error"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/book", methods=["POST"])
def book_ride():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "A valid JSON body is required"}), 400

    user_id = data.get("user_id")
    pickup = str(data.get("pickup", "")).strip()
    destination = str(data.get("destination", "")).strip()
    ride_type = str(data.get("ride_type", "UberGo")).strip()

    if not user_id:
        return jsonify({
            "error": "User ID is required. Please register first."
        }), 400

    try:
        user_id = int(user_id)
        if user_id < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "User ID must be a valid positive integer"}), 400

    if not pickup:
        return jsonify({"error": "Pickup location is required"}), 400
    if not destination:
        return jsonify({"error": "Destination is required"}), 400
    if not ride_type:
        return jsonify({"error": "Ride type is required"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE user_id = %s",
            (user_id,)
        )

        if not cursor.fetchone():
            return jsonify({
                "error": "User not found. Please register first."
            }), 404

        ride_id = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO rides
                (ride_id, user_id, pickup, destination, ride_type, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ride_id,
            user_id,
            pickup,
            destination,
            ride_type,
            "BOOKED"
        ))

        connection.commit()

        return jsonify({
            "message": "Ride booked successfully",
            "ride_id": ride_id,
            "user_id": user_id,
            "pickup": pickup,
            "destination": destination,
            "ride_type": ride_type,
            "status": "BOOKED"
        }), 201

    except Error:
        app.logger.exception("Database error while booking ride")

        if connection and connection.is_connected():
            connection.rollback()

        return jsonify({
            "error": "Unable to book ride due to a database error"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/api/rides", methods=["GET"])
def get_rides():
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        user_id = int(user_id)
        if user_id < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "User ID must be a valid positive integer"}), 400

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT ride_id, pickup, destination, ride_type, status, created_at
            FROM rides
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))

        rows = cursor.fetchall()

        rides = []
        for row in rows:
            rides.append({
                "ride_id": row[0],
                "pickup": row[1],
                "destination": row[2],
                "ride_type": row[3],
                "status": row[4],
                "created_at": str(row[5])
            })

        return jsonify(rides), 200

    except Error:
        app.logger.exception("Database error while retrieving rides")
        return jsonify({
            "error": "Unable to retrieve rides due to a database error"
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    if not connect_with_retry():
        raise SystemExit("Backend stopped because MySQL is unavailable.")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

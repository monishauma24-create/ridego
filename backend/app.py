from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
import mysql.connector
import os
import uuid

app = Flask(__name__)

# Allow frontend on port 8080 to call backend on port 5000
CORS(app)

# Prometheus metrics
metrics = PrometheusMetrics(app)


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "ridebooking"),
        user=os.getenv("DB_USER", "rideuser"),
        password=os.getenv("DB_PASSWORD", "ridepassword"),
        port=int(os.getenv("DB_PORT", "3306"))
    )


def init_db():
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

    cursor.close()
    connection.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "ride-booking-backend"
    })


@app.route("/api/register", methods=["POST"])
def register_user():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    password = data.get("password", "").strip()

    if not name:
        return jsonify({
            "error": "Name is required"
        }), 400

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    if not phone:
        return jsonify({
            "error": "Phone number is required"
        }), 400

    if not password:
        return jsonify({
            "error": "Password is required"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            email,
            phone,
            password
        ))

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

    except mysql.connector.IntegrityError:

        connection.rollback()

        return jsonify({
            "error": "Email or phone number already exists"
        }), 409

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


@app.route("/api/book", methods=["POST"])
def book_ride():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    user_id = data.get("user_id")
    pickup = data.get("pickup", "").strip()
    destination = data.get("destination", "").strip()
    ride_type = data.get("ride_type", "UberGo")

    if not user_id:
        return jsonify({
            "error": "User ID is required. Please register first."
        }), 400

    if not pickup:
        return jsonify({
            "error": "Pickup location is required"
        }), 400

    if not destination:
        return jsonify({
            "error": "Destination is required"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "error": "User not found. Please register first."
            }), 404

        ride_id = str(uuid.uuid4())[:8]

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

    except Exception as error:

        connection.rollback()

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


@app.route("/api/rides", methods=["GET"])
def get_rides():

    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({
            "error": "User ID is required"
        }), 400

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                ride_id,
                pickup,
                destination,
                ride_type,
                status,
                created_at
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

        return jsonify(rides)

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000
    )

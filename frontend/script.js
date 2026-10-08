// =====================================================
// BACKEND URL
// =====================================================

// Replace YOUR_PUBLIC_IP with your EC2 public IP.
// Example:
// const API_URL = "http://16.113.142.207:5000";

const API_URL = "http://16.113.142.207:5000";


// =====================================================
// REGISTER
// =====================================================

const registerForm = document.getElementById("registerForm");

registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const name = document.getElementById("registerName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const phone = document.getElementById("registerPhone").value.trim();
    const password = document.getElementById("registerPassword").value.trim();

    const result = document.getElementById("registerResult");

    result.innerHTML = "Registering...";

    try {

        const response = await fetch(
            `${API_URL}/api/register`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    email: email,
                    phone: phone,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            localStorage.setItem(
                "user_id",
                data.user.user_id
            );

            localStorage.setItem(
                "user_name",
                data.user.name
            );

            result.innerHTML =
                `Registration successful! Welcome ${data.user.name}.`;

            result.style.background = "#e5f7e8";
            result.style.color = "#187a2f";

            registerForm.reset();

        } else {

            result.innerHTML =
                data.error || "Registration failed.";

            result.style.background = "#ffe5e5";
            result.style.color = "#b00020";
        }

    } catch (error) {

        console.error(error);

        result.innerHTML =
            "Unable to connect to server.";

        result.style.background = "#ffe5e5";
        result.style.color = "#b00020";
    }

});


// =====================================================
// BOOK RIDE
// =====================================================

const rideForm = document.getElementById("rideForm");

rideForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const userId = localStorage.getItem("user_id");

    const result = document.getElementById("result");

    if (!userId) {

        result.innerHTML =
            "Please register first before booking a ride.";

        result.style.background = "#ffe5e5";
        result.style.color = "#b00020";

        return;
    }

    const pickup =
        document.getElementById("pickup").value.trim();

    const destination =
        document.getElementById("destination").value.trim();

    const rideType =
        document.getElementById("rideType").value;

    result.innerHTML = "Booking ride...";

    try {

        const response = await fetch(
            `${API_URL}/api/book`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    user_id: userId,
                    pickup: pickup,
                    destination: destination,
                    ride_type: rideType
                })
            }
        );

        const data = await response.json();

        if (response.ok) {

            result.innerHTML =
                `
                <strong>Ride booked successfully!</strong><br>
                Ride ID: ${data.ride_id}<br>
                Status: ${data.status}
                `;

            result.style.background = "#e5f7e8";
            result.style.color = "#187a2f";

            rideForm.reset();

        } else {

            result.innerHTML =
                data.error || "Ride booking failed.";

            result.style.background = "#ffe5e5";
            result.style.color = "#b00020";
        }

    } catch (error) {

        console.error(error);

        result.innerHTML =
            "Unable to connect to server.";

        result.style.background = "#ffe5e5";
        result.style.color = "#b00020";
    }

});


// =====================================================
// LOAD MY RIDES
// =====================================================

async function loadRides() {

    const userId = localStorage.getItem("user_id");

    const rideList = document.getElementById("rideList");

    if (!userId) {

        rideList.innerHTML =
            `
            <div class="ride-item">
                Please register first to view your rides.
            </div>
            `;

        return;
    }

    rideList.innerHTML = "Loading rides...";

    try {

        const response = await fetch(
            `${API_URL}/api/rides?user_id=${userId}`
        );

        const data = await response.json();

        if (!response.ok) {

            rideList.innerHTML =
                `
                <div class="ride-item">
                    ${data.error || "Unable to load rides."}
                </div>
                `;

            return;
        }

        if (data.length === 0) {

            rideList.innerHTML =
                `
                <div class="ride-item">
                    No rides found.
                </div>
                `;

            return;
        }

        rideList.innerHTML = "";

        data.forEach(function (ride) {

            const rideItem =
                document.createElement("div");

            rideItem.className = "ride-item";

            rideItem.innerHTML =
                `
                <h3>Ride #${ride.ride_id}</h3>

                <p>
                    <strong>Pickup:</strong>
                    ${ride.pickup}
                </p>

                <p>
                    <strong>Destination:</strong>
                    ${ride.destination}
                </p>

                <p>
                    <strong>Ride Type:</strong>
                    ${ride.ride_type}
                </p>

                <p>
                    <strong>Date:</strong>
                    ${ride.created_at}
                </p>

                <span class="status">
                    ${ride.status}
                </span>
                `;

            rideList.appendChild(rideItem);

        });

    } catch (error) {

        console.error(error);

        rideList.innerHTML =
            `
            <div class="ride-item">
                Unable to connect to server.
            </div>
            `;
    }
}


// =====================================================
// LOAD RIDES BUTTON
// =====================================================

document
    .getElementById("loadRidesButton")
    .addEventListener("click", loadRides);


// =====================================================
// LOAD RIDES WHEN OPENING MY RIDES
// =====================================================

document
    .querySelector('a[href="#rides"]')
    .addEventListener("click", function () {

        setTimeout(function () {
            loadRides();
        }, 300);

    });

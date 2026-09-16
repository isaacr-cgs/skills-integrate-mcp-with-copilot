document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const calendar = document.getElementById("calendar");

  const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

  function addCalendarItem(items, day, title, schedule, type) {
    if (!items[day]) {
      items[day] = [];
    }
    items[day].push({ title, schedule, type });
  }

  function renderCalendar(activities, events) {
    const items = {};

    Object.entries(activities).forEach(([name, details]) => {
      details.days.forEach((day) => {
        addCalendarItem(items, day, name, details.schedule, "activity");
      });
    });

    Object.entries(events).forEach(([name, details]) => {
      const eventDay = new Date(`${details.date}T00:00:00`).toLocaleDateString(
        "en-US",
        { weekday: "long" }
      );
      addCalendarItem(items, eventDay, name, details.schedule, "event");
    });

    calendar.innerHTML = weekdays
      .map((day) => {
        const dayItems = (items[day] || [])
          .sort((first, second) => first.schedule.localeCompare(second.schedule))
          .map(
            (item) => `
              <li class="calendar-item ${item.type}">
                <strong>${item.title}</strong>
                <span>${item.schedule}</span>
              </li>
            `
          )
          .join("");

        return `
          <div class="calendar-day">
            <h4>${day}</h4>
            ${dayItems ? `<ul>${dayItems}</ul>` : "<p>No activities</p>"}
          </div>
        `;
      })
      .join("");
  }

  function populateSignupOptions(activities, events) {
    activitySelect.innerHTML = '<option value="">-- Select an activity or event --</option>';

    const activityOptions = Object.keys(activities)
      .map((name) => `<option value="activity:${name}">${name}</option>`)
      .join("");
    const eventOptions = Object.keys(events)
      .map((name) => `<option value="event:${name}">${name}</option>`)
      .join("");

    activitySelect.insertAdjacentHTML(
      "beforeend",
      `<optgroup label="Activities">${activityOptions}</optgroup>
       <optgroup label="One-time events">${eventOptions}</optgroup>`
    );
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const [activitiesResponse, eventsResponse] = await Promise.all([
        fetch("/activities"),
        fetch("/events"),
      ]);
      const activities = await activitiesResponse.json();
      const events = await eventsResponse.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      renderCalendar(activities, events);
      populateSignupOptions(activities, events);

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const selection = document.getElementById("activity").value;
    const [type, name] = selection.split(":");
    const endpoint = type === "event" ? "events" : "activities";

    try {
      const response = await fetch(
        `/${endpoint}/${encodeURIComponent(
          name
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.warning
          ? `${result.message} Warning: ${result.warning}`
          : result.message;
        messageDiv.className = result.warning ? "info" : "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});

# Service Agent Bot 🤖

Welcome to the Service Agent Bot! This is a powerful and versatile chatbot built using the Google Agent Development Kit (ADK). It's designed to handle a variety of tasks, making it a one-stop solution for most your automated service needs.

---

## Features

* **🏨 Hotel Booking:** Search for and book hotel rooms.
* **🍔 Food Ordering:** Order your favorite meals from various restaurants.
* **📅 Appointment Scheduling:** Schedule and manage your appointments.
* **💲 Price Listing:** Get real-time price information for various services and products.
* **💳 Payment Processing:** Securely handle payments for all the services offered.
* **🗂️Service Listing:** Get a list of services available for use
* **➕Service Adding:** Add your own services
* **🤝 Unified Coordination:** A central coordinator agent manages the entire workflow, ensuring a smooth and efficient user experience.

---

## 🚀 Getting Started

Getting the Service Agent Bot up and running on your local machine is quick and easy. Just follow these simple steps.

### Prerequisites

Before you begin, make sure you have the following installed on your system:

* [**Docker**](https://www.docker.com/get-started) and [**Docker Compose**](https://docs.docker.com/compose/install/)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/dristiaitech/globalconnector-agent.git
    cd globalconnector-agent
    ```

2.  **Create the Environment File**
    Create a `.env` file in the root directory by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, open the `.env` file and add your credentials and configuration details.

3.  **Build and Run with Docker**
    With Docker running, execute the following command to build and launch the service bot in detached mode:
    ```bash
    docker compose up -d --build
    ```
    The bot is now running and ready to receive requests!

---

## ⚙️ Configuration

The `.env` file is the central place for all your configuration needs. Here's a breakdown of the variables:

* `GOOGLE_API_KEY`: Your API key for Google LLM model services.
* `GOOGLE_GENAI_USE_VERTEXAI`: Set to `1` to use Vertex AI, or `0` to use another service.
* `SERVICE_BOT_HOST`: The host for the service bot API (e.g., `0.0.0.0`).
* `SERVICE_BOT_PORT`: The port for the service bot API (e.g., `8000`).
* `AUTH_SECRET_KEY`: Secret key for authentication.
* `AUTH_ALGORITHM`: Algorithm used for authentication.
* `PAYMENT_API_URL`: URL for the payment API.

## 📂 Project Structure

The project is organized to be modular and scalable. Here's a look at the key directories:
```
.
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── compose.yml
├── config
│   ├── __init__.py
│   ├── config.py
│   └── logger.py
├── data
│   ├── appointment.json
│   ├── created_services.json
│   ├── nearby_hotel.json
│   ├── nearby_restaurants.json
│   ├── orders.json
│   └── prices.json
├── Dockerfile
├── logs
│   └── .gitkeep
├── pyproject.toml
├── README.md
├── ruff.toml
├── src
│   └── globalconnector_agent
│       ├── core
│       │   ├── __init__.py
│       │   ├── agents
│       │   │   ├── appointment.py
│       │   │   ├── base.py
│       │   │   ├── booking.py
│       │   │   ├── coordinator.py
│       │   │   ├── ordering.py
│       │   │   ├── payment.py
│       │   │   ├── prices.py
│       │   │   ├── service_add.py
│       │   │   └── service_use.py
│       │   ├── prompts.py
│       │   ├── service.py
│       │   └── tools
│       │       ├── appointment.py
│       │       ├── booking.py
│       │       ├── ordering.py
│       │       ├── payment.py
│       │       ├── prices.py
│       │       └── services.py
│       ├── main.py
│       ├── routers
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── data_model.py
│       └── utils
│           ├── __init__.py
│           └── utils.py
└── uv.lock
```

## 🔌 API Endpoints

The Service Agent Bot exposes the following API endpoints:

### Health Check

* **Endpoint:** `/api/`
* **Method:** `GET`
* **Description:** A simple health check to confirm that the service is up and running.
* **Success Response:**
    ```json
    {
      "message": "Service bot is running!"
    }
    ```

### Service Bot

* **Endpoint:** `/api/service_bot`
* **Method:** `POST`
* **Description:** The main endpoint to interact with the agent. Send your requests here to be processed.
* **Request Body:**
    ```json
    {
      "user_message": "I want to book a hotel in Hanoi for two nights.",
      "user_id": "user-123",
      "request_id": "session-456"
    }
    ```
* **Success Response:**
    ```json
    {
      "status": "success",
      "response": "Of course! I can help with that. When would you like to check in?"
    }
    ```
* **Error Response:**
    ```json
    {
      "status": "error",
      "detail": "Error processing update: [error message]"
    }
    ```

### How to Use

You can interact with the bot using any HTTP client. Here's an example using `curl`:

```bash
curl -X POST http://localhost:8000/api/service_bot \
-H "Content-Type: application/json" \
-d '{
  "user_message": "I need a hotel room for two people tomorrow",
  "user_id": "user-123",
  "request_id": "session-789"
}'

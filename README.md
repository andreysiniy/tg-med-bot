# Telegram Medical Appointment Bot (tg-med-bot)

A sophisticated Telegram bot designed to streamline the process of managing medical appointments. It leverages Google's Gemini for Natural Language Understanding (NLU) to interpret user requests, allowing for intuitive interactions. Users can book, view, reschedule, and cancel appointments through a guided conversational flow or by using natural language.

## Features

-   **Natural Language Processing:** Understands user intents like booking, viewing, rescheduling, or canceling appointments using Google Gemini.
-   **Conversational UI:** A step-by-step process guides users through booking and editing appointments with interactive keyboards.
-   **CRUD Operations:** Full support for Creating, Reading, Updating, and Deleting (CRUD) appointments.
-   **Backend Integration:** Communicates with a separate backend service to manage all data related to clinics, doctors, schedules, and appointments.
-   **User Management:** Registers and stores user information in a MongoDB database, linking their Telegram profile to an internal user ID.

## Project Structure

The project is organized into several modules to ensure a clean separation of concerns:

```
└── tg-med-bot/
    ├── main.py                     # Main entry point of the application
    ├── config.ini                  # Configuration file for API tokens and settings
    ├── requirements.txt            # Python dependencies
    ├── bot/
    │   └── telegram_bot_initializer.py # Initializes the bot, handlers, and conversation flows
    ├── clients/
    │   └── backend_api_client.py   # Handles communication with the external backend API
    ├── db/
    │   └── mongodb_service.py      # Manages interaction with the MongoDB database
    ├── handlers/
    │   ├── create_step_handler.py  # Logic for the new appointment conversation
    │   ├── edit_handler.py         # Logic for rescheduling an appointment
    │   ├── delete_handler.py       # Logic for canceling an appointment
    │   └── view_handler.py         # Logic for displaying a user's appointments
    ├── helpers/
    │   └── configurator.py         # Helper to read the config.ini file
    └── llmservices/
        └── google_service.py       # Service to interact with the Google Gemini API
```

## Technologies Used

-   **Language:** Python 3.11
-   **Telegram Framework:** `python-telegram-bot`
-   **Database:** MongoDB with `pymongo`
-   **AI/NLU:** Google Gemini via `google-genai`
-   **HTTP Client:** `aiohttp`

## Setup and Installation

Follow these steps to get the bot running on your local machine.

### 1. Prerequisites

-   Python 3.11+
-   A running MongoDB instance.
-   A running instance of the required **backend API service**. The bot is hardcoded to expect this service at `http://localhost:5136`.

### 2. Clone the Repository

```bash
git clone https://github.com/andreysiniy/tg-med-bot.git
cd tg-med-bot
```

### 3. Create a Virtual Environment (Recommended)

```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure the Bot

Create a file named `config.ini` in the root directory of the project. This file will hold your secret keys and settings. **Do not commit this file to version control.**

Your `config.ini` file should look like this:

```ini
[TELEGRAM]
token = YOUR_TELEGRAM_BOT_TOKEN_FROM_BOTFATHER

[GOOGLE]
token = YOUR_GOOGLE_AI_API_KEY
model = gemini-2.5-flash-latest
```

-   **`[TELEGRAM] token`**: Get this from BotFather on Telegram.
-   **`[GOOGLE] token`**: Your API key from Google AI Studio.
-   **`[GOOGLE] model`**: The Gemini model you wish to use (e.g., `gemini-2.5-flash-latest`).

### 6. Run the Bot

Ensure your MongoDB and backend API services are running, then start the bot:

```bash
python main.py
```

The bot should now be online and responsive on Telegram.

## How It Works

The application's workflow is as follows:

1.  A user sends a message to the Telegram bot.
2.  If the message is not a recognized command, it is treated as a natural language query and passed to the `default_response` function.
3.  This function sends the user's text to the `GoogleService`, which uses the Gemini model to parse the request. It returns a JSON object with the user's `intent` (e.g., `book_appointment`) and any extracted `data` (like a doctor's name or a specific date).
4.  Based on the returned `intent`, the bot's `telegram_bot_initializer` directs the conversation to the appropriate handler (`CreateStepHandler`, `EditHandler`, etc.).
5.  These handlers manage a multi-step `ConversationHandler` to gather all necessary information from the user by presenting them with interactive keyboards (e.g., select clinic, doctor, date, and time).
6.  Throughout the process, the `BackendApiClient` communicates with the external API to fetch data (e.g., getting a list of available doctors) and to create, update, or delete appointments.
7.  The `mongodb_service` manages user data, linking their Telegram ID to an internal UUID that is used in API calls.

## Usage

You can interact with the bot using both specific commands and natural language.

#### Commands

-   `/start` - Initializes the bot, displays a welcome message, and registers the user if they are new.
-   `/new_appointment` - Explicitly starts the step-by-step process for booking a new appointment.
-   `/cancel` - Use this command during any multi-step process (like booking or editing) to cancel the current action.

#### Natural Language Examples

The bot's main strength is understanding plain text. You can simply tell it what you want to do:

-   *"I'd like to book an appointment with a cardiologist"*
-   *"Show me my upcoming appointments"*
-   *"I need to reschedule my appointment with Dr. House"*
-   *"Cancel my appointment for next Tuesday"*

## External Dependencies

This bot relies on two external services to function correctly:

-   **MongoDB:** A NoSQL database used for storing user profiles. The connection URI is currently hardcoded in `db/mongodb_service.py` to `mongodb://localhost:27017/`.
-   **Backend API:** A separate backend application that manages all medical data (clinics, doctors, appointments, etc.). The bot is configured to communicate with this API at `http://localhost:5136/api/` as defined in `clients/backend_api_client.py`. **This service is a hard dependency and must be running for the bot to work.**

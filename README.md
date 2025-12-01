# 🤖 ESTIN University Chatbot (AI Assistant)

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Local Setup and Installation](#3-local-setup-and-installation)
4. [Training the Model](#4-training-the-model)


---

## 1. Project Overview

This is an AI-powered conversational chatbot built with **Flask** and **PyTorch** designed to assist students of ESTIN University with frequently asked questions (FAQs).

The chatbot uses a **Feedforward Neural Network (FNN)** to classify user intent based on the text input, and then retrieves the corresponding static or dynamic response from the structured `faq_data.json` knowledge base. It also supports serving academic files (schedules, PDFs).

**Key Technologies:**
* **Backend:** Python, Flask
* **AI/ML:** PyTorch, NLTK
* **Deployment:** Gunicorn, Procfile

---

## 2. Features

* **Intent Recognition:** Classifies user queries (e.g., "greeting," "library\_opening," "exam\_schedule") using a trained neural network.
* **Rule-Based Responses:** Provides static answers for common queries (hours, fees, deadlines). (This is an old version and is not the one that's currently served on the web interface)
* **File Serving:** Serves static academic resources like semester schedules and administrative PDFs directly to the user interface.
* **Modular Design:** Separates the Flask application (`app.py`), neural network logic (`chat.py`), and data (`faq_data.json`).

---

## 3. Local Setup and Installation

Follow these steps to get a local copy of the project running for development.

### Prerequisites

* Python 3.8+
* Git

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone [Your-GitHub-Repository-URL]
    cd estin-chatbot
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named **`.env`** in the root directory and add your secret key:

    ```ini
    # .env
    SECRET_KEY='your_strong_secret_key_here'
    FLASK_APP=app.py
    FLASK_DEBUG=True
    ```

5.  **Run the Application:**
    ```bash
    python app.py
    # or
    flask run
    ```
    The application will run at `http://127.0.0.1:5000/`.

---

## 6. Training the Model

The model is trained based on the data in `faq_data.json`. The trained weights are saved to `data.pth`.

If you update the `faq_data.json` file (add new intents, patterns, or responses), you must retrain the model:

```bash
python chat.py

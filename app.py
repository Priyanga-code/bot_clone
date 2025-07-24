from flask import Flask, render_template, request
import joblib
from groq import Groq
import os
import requests
import sqlite3

# Get your Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Flask app
app = Flask(__name__)

# Home page
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

# Main page
@app.route("/main", methods=["GET", "POST"])
def main():
    return render_template("main.html")

# LLAMA chatbot via Groq
@app.route("/llama", methods=["GET", "POST"])
def llama():
    return render_template("llama.html")

@app.route("/llama_reply", methods=["GET", "POST"])
def llama_reply():
    q = request.form.get("q")
    client = Groq()
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": q}]
    )
    return render_template("llama_reply.html", r=completion.choices[0].message.content)

# DeepSeek chatbot via Groq
@app.route("/deepseek", methods=["GET", "POST"])
def deepseek():
    return render_template("deepseek.html")

@app.route("/deepseek_reply", methods=["GET", "POST"])
def deepseek_reply():
    q = request.form.get("q")
    client = Groq()
    completion_ds = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[{"role": "user", "content": q}]
    )
    return render_template("deepseek_reply.html", r=completion_ds.choices[0].message.content)

# Predict DBS stock price
@app.route("/dbs", methods=["GET", "POST"])
def dbs():
    return render_template("dbs.html")

@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    q = float(request.form.get("q"))
    model = joblib.load("dbs.jl")
    pred = model.predict([[q]])
    return render_template("prediction.html", r=pred)

# Telegram bot setup
@app.route("/telegram", methods=["GET", "POST"])
def telegram():
    domain_url = 'https://bot-clone-f8er.onrender.com'
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    set_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={domain_url}/webhook"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    status = "The telegram bot is running." if webhook_response.status_code == 200 else "Failed to start the telegram bot."
    return render_template("telegram.html", r=status)

@app.route("/stop_telegram", methods=["GET", "POST"])
def stop_telegram():
    domain_url = 'https://bot-clone-f8er.onrender.com'
    delete_webhook_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    webhook_response = requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})

    status = "The telegram bot has stopped." if webhook_response.status_code == 200 else "Failed to stop the telegram bot."
    return render_template("stop_telegram.html", r=status)

# Telegram Webhook endpoint
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        query = update["message"]["text"]

        client = Groq()
        completion_ds = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[{"role": "user", "content": query}]
        )

        response_message = completion_ds.choices[0].message.content
        send_message_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(send_message_url, json={"chat_id": chat_id, "text": response_message})
    return 'ok', 200

# View and delete user logs from SQLite
@app.route("/user_log", methods=["GET", "POST"])
def user_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    try:
        c.execute('SELECT * FROM user')
        rows = c.fetchall()
        log_str = "\n".join([f"{row[0]} - {row[1]}" for row in rows]) if rows else "No logs found."
    except sqlite3.OperationalError:
        log_str = "Table 'user' does not exist."
    c.close()
    conn.close()
    return render_template("user_log.html", r=log_str)

@app.route("/delete_log", methods=["GET", "POST"])
def delete_log():
    conn = sqlite3.connect('user.db')
    c = conn.cursor()
    try:
        c.execute('DELETE FROM user')
        conn.commit()
        result = "All user logs have been deleted."
    except sqlite3.OperationalError:
        result = "Table 'user' does not exist."
    c.close()
    conn.close()
    return render_template("delete_log.html", r=result)

# Gradio Sepia Embed Page
@app.route("/sepia", methods=["GET", "POST"])
def sepia():
    return render_template("sepia.html")

# Run app with host and port for Render deployment
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
from flask import Flask, render_template, request, jsonify
import sqlite3
from openai import OpenAI

app = Flask(__name__)

# =========================
# OPENAI CLIENT
# =========================
client = OpenAI(api_key="api_key_here)"


# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================
# MEMORY FUNCTIONS
# =========================
def save_message(role, content):
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("DB SAVE ERROR:", e)


def load_memory(limit=10):
    try:
        conn = sqlite3.connect("memory.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )

        rows = cursor.fetchall()
        conn.close()

        # reverse to keep conversation order
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    except Exception as e:
        print("DB LOAD ERROR:", e)
        return []


# =========================
# ROUTES
# =========================
@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        # =========================
        # SAFE JSON PARSING
        # =========================
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        # save user message
        save_message("user", user_message)

        history = load_memory()

        # =========================
        # SYSTEM PROMPT
        # =========================
        system_prompt = """
You are a professional content strategist and viral idea generator.

Rules:
- Give high quality, actionable ideas
- Avoid generic advice
- Include hook + explanation + platform suggestion
- Be structured and clear
You are a professional Social Media Content Strategist and Viral Idea Generator.

Your job is to generate high-performing, platform-optimized content ideas that can grow engagement, followers, and conversions on social media.

You specialize in understanding current internet trends, audience psychology, and platform algorithms (TikTok, Instagram, YouTube Shorts, X/Twitter, LinkedIn).

---

## INPUTS YOU WILL RECEIVE:
- Niche: {user_niche}
- Platform: {platform}
- Audience: {target_audience}
- Goal: {goal: growth / engagement / sales / education / branding}
- Tone: {tone: funny, professional, motivational, relatable, etc.}

---

## YOUR TASK:
Generate 10–15 viral content ideas tailored to the input.

Each idea must include:

1. **Hook (first 1–3 seconds / first line)**
   - Must grab attention immediately
   - Should trigger curiosity, emotion, or controversy

2. **Content Idea**
   - Clear explanation of what the post/video is about

3. **Format Type**
   - (Reel, Short, Carousel, Thread, Story, Meme, Educational post, etc.)

4. **Why it works**
   - Brief psychology or trend reasoning (e.g., “uses curiosity gap”, “relatable pain point”, “trend hijacking”)

5. **Optional Viral Angle**
   - Suggest how to make it more shareable or trend-friendly

---

## RULES:
- Avoid generic ideas
- Do NOT repeat templates
- Prioritize trending, scroll-stopping concepts
- Use real social media style language (not academic tone)
- Think like a viral creator, not a textbook
- Include modern internet slang when appropriate (but not overused)
- Ideas must be realistic and actually postable today

---

## OUTPUT FORMAT:

For each idea:

### Idea 1
Hook:
Content:
Format:
Why it works:
Viral twist:

(repeat…)

---

## EXTRA INTELLIGENCE LAYER:
Always consider:
- Current trends on TikTok, Instagram Reels, YouTube Shorts
- Attention span (first 2 seconds matter most)
- Emotional triggers: curiosity, fear of missing out, shock, relatability, humor
- Shareability factor

---

Now generate content ideas based on the user inputs.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message}
        ]

        # =========================
        # OPENAI CALL (SAFE)
        # =========================
        try:
            response = client.chat.completions.create(
                model="gpt-3o-mini",
                messages=messages
            )

            reply = response.choices[0].message.content

        except Exception as ai_error:
            print("OPENAI ERROR:", ai_error)
            return jsonify({"error": "reconnect to a better network"}), 500

        # save assistant response
        save_message("assistant", reply)

        return jsonify({"reply": reply})

    except Exception as bad_network:
        print("CHAT ROUTE ERROR:", bad_network)
        return jsonify({"error": str(bad_network)}), 500


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
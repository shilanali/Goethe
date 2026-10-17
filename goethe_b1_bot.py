"""
Goethe B1 daily practice poster for a Telegram channel (no AI API needed).
Reads today's exercise from content.json and posts text/audio + quiz polls.

Env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL (e.g. @my_b1_german)
Optional: START_DATE (YYYY-MM-DD, default 2026-10-18) = day 1 of the cycle.
"""
import os, json, datetime, requests
from gtts import gTTS

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL = os.environ["TELEGRAM_CHANNEL"]
START = datetime.date.fromisoformat(os.environ.get("START_DATE", "2026-10-18"))
API = f"https://api.telegram.org/bot{TOKEN}"

TITLES = {"lesen": "Lesen 📖", "hoeren": "Hören 🎧",
          "grammatik": "Grammatik ✍️", "wortschatz": "Wortschatz 🔤"}


def send(method, files=None, **kw):
    r = requests.post(f"{API}/{method}", data=kw, files=files, timeout=60)
    if not r.ok:
        raise SystemExit(f"Telegram error: {r.text}")


def main():
    with open("content.json", encoding="utf-8") as f:
        bank = json.load(f)
    day = (datetime.date.today() - START).days
    item = bank[day % len(bank)]
    skill = item["skill"]

    send("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
         text=f"📚 <b>Goethe B1 – {TITLES[skill]}</b>\nTag {day % len(bank) + 1}/{len(bank)} · Thema: {item['topic']}")

    if skill == "hoeren":
        gTTS(item["text"], lang="de").save("audio.mp3")
        with open("audio.mp3", "rb") as f:
            send("sendAudio", files={"audio": f}, chat_id=CHANNEL,
                 title=f"Hören – {item['topic']}")
        send("sendMessage", chat_id=CHANNEL,
             text="🎧 Hör zu (mehrmals) und beantworte die Fragen.")
    else:
        send("sendMessage", chat_id=CHANNEL, text=item["text"])

    for q in item["questions"]:
        send("sendPoll", chat_id=CHANNEL, question=q["q"][:300], type="quiz",
             options=json.dumps(q["options"], ensure_ascii=False),
             correct_option_id=q["correct"], is_anonymous="true",
             explanation=q["explanation"][:200])

    if skill == "hoeren":
        send("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
             text="Transkript zur Kontrolle (antippen):\n<tg-spoiler>"
                  + item["text"] + "</tg-spoiler>")


if __name__ == "__main__":
    main()

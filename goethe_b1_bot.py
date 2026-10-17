"""
Goethe B1 practice poster for a Telegram channel (no AI API needed).
Runs every 2 hours from 06:00 to 22:00 Damascus time (9 posts/day).
- 06:00: good-morning message, then the first exercise
- 22:00: last exercise, then a good-night message
Exercises come from content*.json files (content.json, content2.json, ...).

Env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL (e.g. @my_b1_german)
Optional: START_DATE (YYYY-MM-DD, default 2026-10-18) = day 1.
"""
import os, json, glob, datetime, requests
from zoneinfo import ZoneInfo
from gtts import gTTS

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL = os.environ["TELEGRAM_CHANNEL"]
START = datetime.date.fromisoformat(os.environ.get("START_DATE", "2026-10-18"))
API = f"https://api.telegram.org/bot{TOKEN}"
SLOTS_PER_DAY = 9          # 06,08,10,12,14,16,18,20,22
FIRST_HOUR, STEP = 6, 2

TITLES = {"lesen": "Lesen 📖", "hoeren": "Hören 🎧",
          "grammatik": "Grammatik ✍️", "wortschatz": "Wortschatz 🔤"}

GREETINGS = [
    "☀️ Guten Morgen!  SUNSHINE 💪",
    "🌅 Guten Morgen und herzlich willkommen! أهلاً بك في يوم جديد من التدريب.\nتمرين صغير كل ساعتين. خطوة بخطوة نحو B1! 🎯",
    "☕ Guten Morgen! صباح النور!\nاستعد ليوم جديد من الألمانية. أول تمرين الآن 👇",
    "🌞 Hallo und guten Morgen! يوم موفق!\nالاستمرار أهم من الكمال. هيا نتدرب! 🚀",
]
FAREWELLS = [
    "🌙 Gute Nacht SUNSHINE! تصبح على خير!\nأحسنت اليوم 👏   .",
    "🌟 Das war's für heute! انتهت تمارين اليوم.\nأحسنت على الالتزام، وراجع الأسئلة التي أخطأت فيها قبل النوم. Gute Nacht! 😴",
    "🌃 Schönen Abend noch! مساء الخير وتصبح على خير.\nكل يوم تدريب يقرّبك من النجاح في امتحان B1. Bis morgen! 👋",
    "🌙 Gute Nacht und bis morgen! إلى اللقاء غداً.\nاستراحة المحارب تبدأ الآن، وغداً نواصل بقوة 💪",
]


def send(method, files=None, **kw):
    r = requests.post(f"{API}/{method}", data=kw, files=files, timeout=60)
    if not r.ok:
        raise SystemExit(f"Telegram error: {r.text}")


def load_bank():
    bank = []
    for path in sorted(glob.glob("content*.json")):
        with open(path, encoding="utf-8") as f:
            bank += json.load(f)
    return bank


def main():
    now = datetime.datetime.now(ZoneInfo("Asia/Damascus"))
    day = (now.date() - START).days
    slot = min(max((now.hour - FIRST_HOUR) // STEP, 0), SLOTS_PER_DAY - 1)

    bank = load_bank()
    n = day * SLOTS_PER_DAY + slot
    item = bank[n % len(bank)]
    skill = item["skill"]

    if slot == 0:
        send("sendMessage", chat_id=CHANNEL, text=GREETINGS[day % len(GREETINGS)])

    send("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
         text=f"📚 <b>Goethe B1 – {TITLES[skill]}</b>\n"
              f"Übung {slot + 1}/{SLOTS_PER_DAY} · Thema: {item['topic']}")

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

    if slot == SLOTS_PER_DAY - 1:
        send("sendMessage", chat_id=CHANNEL, text=FAREWELLS[day % len(FAREWELLS)])


if __name__ == "__main__":
    main()

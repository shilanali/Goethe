"""
Goethe B1 practice poster for a Telegram channel (no AI API needed).
3 gentle posts per day (Damascus time): 08:00, 14:00, 20:00
- first post: good-morning + countdown to New Year (registration goal) + encouragement
- last post: exercise, then a calm good-night message
Exercises come from content*.json files (content.json, content2.json, ...).

Env vars: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL (e.g. @my_b1_german)
Optional: START_DATE (default 2026-10-18), DEADLINE (default 2026-12-31)
To go back to every 2 hours: set HOURS = [6,8,10,12,14,16,18,20,22]
and use cron "0 3,5,7,9,11,13,15,17,19 * * *" in daily.yml.
"""
import os, json, glob, datetime, requests
from zoneinfo import ZoneInfo
from gtts import gTTS

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL = os.environ["TELEGRAM_CHANNEL"]
START = datetime.date.fromisoformat(os.environ.get("START_DATE", "2026-10-18"))
DEADLINE = datetime.date.fromisoformat(os.environ.get("DEADLINE", "2026-12-31"))
API = f"https://api.telegram.org/bot{TOKEN}"
HOURS = [8, 14, 20]        # Damascus time

TITLES = {"lesen": "Lesen 📖", "hoeren": "Hören 🎧",
          "grammatik": "Grammatik ✍️", "wortschatz": "Wortschatz 🔤"}

GREETINGS = [
    "☀️ Guten Morgen SunShine !\nتمرين صغير الآن، وتمرين آخر في الظهر، وثالث في المساء. وإن لم تتمكن اليوم، فتمرين واحد يكفي 💛",
    "🌅 Guten Morgen SunShine !\nلا ضغط ولا التزام ثقيل: حلّ ما تستطيع، ومتى تستطيع. المهم أن تستمر 🌱",
    "☕ Hallo und guten Morgen!\nثلاثة تمارين قصيرة اليوم، كل واحد يحتاج دقائق فقط ⏱️",
    "🌞 Guten Morgen! يلا بارتنر تمرين صغير بس "
MOTIVATION = [
    "💡 لا أحد يبدأ جاهزاً 100%. الامتحان يقيس مستواك الحالي، وليس قيمتك ولا ذكاءك.",
    "💡 الخوف طبيعي، لكن خطوة التسجيل هي الأهم. بعدها كل شيء يصبح أسهل.",
    "💡 ليكي ولي هيفاء معك شهرين تقدمي هالفحص السنة الجديدة بدك تهديني خبر نجاحك ",
    "💡 قرار التقديم قبل رأس السنة هدية تقدمها لمستقبلك. أنت قادر 💪",
    "💡 كل كلمة جديدة تتعلمها اليوم تقرّبك من B1، حتى لو كانت كلمة واحدة.",
]
FAREWELLS = [
    "🌙 Gute Nacht SunShine!.\nأحسنت مهما حللت اليوم 👏 نلتقي غداً بتمارين جديدة.",
    "🌟 Das war's für heute SunShine! سواء حللت كل التمارين أو واحداً فقط، أنت تتقدّم.\nGute Nacht! 😴",
    "🌃 Schönen Abend SunShine!.\nخذ قسطاً من الراحة، وغداً يوم جديد. Bis morgen! 👋",
    "🌙 Gute Nacht SunShine! إلى اللقاء غداً.\nلا تقلق من التأخر، نبدأ من حيث وصلت 🤍",
    "2027 هيفاء في ألمانيا"
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


def countdown(today):
    d = (DEADLINE - today).days
    if d > 1:
        return f"⏳ باقي {d} يوماً على رأس السنة، موعدك للتقديم لامتحان غوته."
    if d == 1:
        return "⏳ باقي يوم واحد على رأس السنة. هذه فرصتك للتقديم، لا تؤجل 💪"
    if d == 0:
        return "⏳ اليوم آخر يوم قبل رأس السنة. قدّم اليوم، أنت جاهز أكثر مما تظن 💪"
    return "🎯 حان وقت الإنجاز: سجّل في الامتحان وانطلق، وما نتدرب عليه يكفي لتبدأ."


def main():
    now = datetime.datetime.now(ZoneInfo("Asia/Damascus"))
    today = now.date()
    day = (today - START).days
    slot = max([i for i, h in enumerate(HOURS) if now.hour >= h] or [0])

    bank = load_bank()
    item = bank[(day * len(HOURS) + slot) % len(bank)]
    skill = item["skill"]

    if slot == 0:
        send("sendMessage", chat_id=CHANNEL,
             text=GREETINGS[day % len(GREETINGS)] + "\n\n" + countdown(today)
                  + "\n\n" + MOTIVATION[day % len(MOTIVATION)])

    send("sendMessage", chat_id=CHANNEL, parse_mode="HTML",
         text=f"📚 <b>Goethe B1 – {TITLES[skill]}</b>\nThema: {item['topic']}")

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

    if slot == len(HOURS) - 1:
        send("sendMessage", chat_id=CHANNEL, text=FAREWELLS[day % len(FAREWELLS)])


if __name__ == "__main__":
    main()

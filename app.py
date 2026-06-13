import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic

app = App(token=os.environ["SLACK_BOT_TOKEN"])
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = "あなたは転職エージェントの寺尾美里（株式会社フューチャーリンク）として、候補者へ初回面談の日程調整メールを書きます。温かみがあり距離感を縮める言い回しを使い、丁寧だが堅苦しくない誠実でフラットな敬語を使います。AIっぽい表現は避け、稀有・証左・感銘・確信は使用禁止。太字・記号は使わない。以下の構成で書いてください。1.宛名 2.株式会社フューチャーリンクの寺尾です。返信へのお礼 3.スカウト理由（レジュメから具体的に）＋是非お会いしたい！！と思いを込めてスカウトをさせていただいたので、ご返信いただけてとても嬉しいです！は必須 4.返信への応答（ある場合） 5.面談でお聞きしたいこと 6.フラットな情報交換の場であること 7.URL: https://app.spirinc.com/t/InyWmdvIrhOuv-hw7uFwP/as/f-GFwOt7-Vfv484_rVcgQ/confirm 8.30分から45分程度 9.締め 10.署名:フューチャーリンク 寺尾"

USAGE_GUIDE = "*使い方*\n以下の形式で送ってください\n\n【候補者名】山田 太郎\n\n【レジュメ】\n（レジュメを貼り付け）\n\n【返信文】\n（返信を貼り付け。なければ「なし」）"


def parse_message(text):
    name_match = re.search(r'[\u300c\u300e\u3010]候補者名[\u300d\u300f\u3011]\s*(.+)', text)
    if not name_match:
        name_match = re.search(r'\u3010候補者名\u3011\s*(.+)', text)
    resume_match = re.search(r'\u3010レジュメ\u3011\s*([\s\S]+?)(?=\u3010返信文\u3011|$)', text)
    reply_match = re.search(r'\u3010返信文\u3011\s*([\s\S]+?)$', text)
    name = name_match.group(1).strip() if name_match else None
    resume = resume_match.group(1).strip() if resume_match else None
    reply = reply_match.group(1).strip() if reply_match else ""
    if not reply or reply.lower() in ["nashi", "none"]:
        reply = ""
    if reply == "\u306a\u3057":
        reply = ""
    return name, resume, reply


def generate_mail(name, resume, reply):
    reply_text = reply if reply else "(返信なし)"
    user_prompt = "候補者名: " + name + "\n\nレジュメ\n" + resume + "\n\n返信文\n" + reply_text + "\n\n初回面談日程調整メールを作成してください。"
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text


@app.event("app_mention")
def handle_mention(event, say):
    text = re.sub(r'<@[A-Z0-9]+>', '', event.get("text", "")).strip()
    if not text or "使い方" in text or "help" in text.lower():
        say(USAGE_GUIDE)
        return
    name, resume, reply = parse_message(text)
    if not name or not resume:
        say("候補者名またはレジュメが見当たりませんでした。\n\n" + USAGE_GUIDE)
        return
    say("メールを生成中です... :writing_hand:")
    try:
        mail = generate_mail(name, resume, reply)
        say("```\n" + mail + "\n```")
    except Exception as e:
        say("エラーが発生しました。もう一度試してください。\n" + str(e))


@app.event("message")
def handle_dm(event, say):
    if event.get("channel_type") != "im":
        return
    text = event.get("text", "").strip()
    if not text or "使い方" in text or "help" in text.lower():
        say(USAGE_GUIDE)
        return
    name, resume, reply = parse_message(text)
    if not name or not resume:
        say("候補者名またはレジュメが見当たりませんでした。\n\n" + USAGE_GUIDE)
        return
    say("メールを生成中です... :writing_hand:")
    try:
        mail = generate_mail(name, resume, reply)
        say("```\n" + mail + "\n```")
    except Exception as e:
        say("エラーが発生しました。もう一度試してください。")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

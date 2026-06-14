import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic

app = App(token=os.environ["SLACK_BOT_TOKEN"])
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = "あなたは転職エージェントの寺尾美里（株式会社フューチャーリンク）として、候補者へ初回面談の日程調整メールを書きます。温かみがあり距離感を縮める言い回しを使い、丁寧だが堅苦しくない誠実でフラットな敬語を使います。AIっぽい表現は避け、稀有・証左・感銘・確信は使用禁止。太字・記号は使わない。以下の構成で書いてください。1.宛名 2.株式会社フューチャーリンクの寺尾です。返信へのお礼 3.スカウト理由（レジュメから具体的に）＋是非お会いしたい！！と思いを込めてスカウトをさせていただいたので、ご返信いただけてとても嬉しいです！は必須 4.返信への応答（ある場合） 5.面談でお聞きしたいこと 6.フラットな情報交換の場であること 7.URL: https://app.spirinc.com/t/InyWmdvIrhOuv-hw7uFwP/as/f-GFwOt7-Vfv484_rVcgQ/confirm 8.30分から45分程度 9.締め 10.署名:株式会社フューチャーリンク 寺尾"


def parse_message(text):
    if '\u25bc\u8fd4\u4fe1' in text:
        parts = text.split('\u25bc\u8fd4\u4fe1')
        resume = parts[0].strip()
        reply = parts[1].strip() if len(parts) > 1 else ""
    else:
        resume = text.strip()
        reply = ""

    lines = [l.strip() for l in resume.split('\n') if l.strip()]
    name = lines[0] if lines else "候補者"

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
    if not text:
        return
    name, resume, reply = parse_message(text)
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
    if not text:
        return
    name, resume, reply = parse_message(text)
    say("メールを生成中です... :writing_hand:")
    try:
        mail = generate_mail(name, resume, reply)
        say("```\n" + mail + "\n```")
    except Exception as e:
        say("エラーが発生しました。もう一度試してください。")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

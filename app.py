import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic

app = App(token=os.environ["SLACK_BOT_TOKEN"])
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """あなたは転職エージェントの寺尾美里（フューチャーリンクス株式会社）として、候補者へ初回面談の日程調整メールを書きます。

【キャラクター】
- IT・ネット業界のマネージャー層以上を専門とする転職エージェント
- 温かみがあり、距離感を縮める言い回しを使う
- 丁寧だが堅苦しくない、誠実でフラットな敬語

【文章ルール】
- AIっぽい表現は避ける
- 「稀有」「証左」「感銘」「確信」は使用禁止
- 太字・記号は使わない
- 「{NAME}様のこれまでの歩みを拝見いたしました」禁止

【構成】
1. 宛名
2. 株式会社フューチャーリンクの寺尾です。返信へのお礼
3. スカウト理由（レジュメから具体的に）＋「是非お会いしたい！！と思いを込めてスカウトをさせていただいたので、ご返信いただけてとても嬉しいです！」は必須
4. 返信への応答（ある場合）
5. 面談でお聞きしたいこと
6. フラットな情報交換の場であること
7. URL：https://app.spirinc.com/t/InyWmdvIrhOuv-hw7uFwP/as/f-GFwOt7-Vfv484_rVcgQ/confirm
8. 30分〜45分程度
9. 締め
10. 署名：フューチャーリンク 寺尾"""

USAGE_GUIDE = """*使い方*
以下の形式で送ってください：
【候補者名】山田 太郎
【レジュメ】

（レジュメを貼り付け）
【返信文】

（返信を貼り付け。なければ「なし」）
def parse_message(text):
    name_match = re.search(r'【候補者名】\s*(.+)', text)
    resume_match = re.search(r'【レジュメ】\s*([\s\S]+?)(?=【返信文】|$)', text)
    reply_match = re.search(r'【返信文】\s*([\s\S]+?)$', text)
    name = name_match.group(1).strip() if name_match else None
    resume = resume_match.group(1).strip() if resume_match else None
    reply = reply_match.group(1).strip() if reply_match else ""
    if reply.lower() in ["なし", "none", ""]:
        reply = ""
    return name, resume, reply

def generate_mail(name, resume, reply):
    user_prompt = f"""候補者名：{name}

【レジュメ】
{resume}

【返信文】
{reply if reply else "（返信なし）"}

初回面談日程調整メールを作成してください。"""
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
        say(f"候補者名またはレジュメが見当たりませんでした。\n\n{USAGE_GUIDE}")
        return
    say("メールを生成中です... :writing_hand:")
    try:
        mail = generate_mail(name, resume, reply)
        say(f"```\n{mail}\n```")
    except Exception as e:
        say(f"エラーが発生しました。もう一度試してください。\n{str(e)}")

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
        say(f"候補者名またはレジュメが見当たりませんでした。\n\n{USAGE_GUIDE}")
        return
    say("メールを生成中です... :writing_hand:")
    try:
        mail = generate_mail(name, resume, reply)
        say(f"```\n{mail}\n```")
    except Exception as e:
        say(f"エラーが発生しました。もう一度試してください。")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()

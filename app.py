import os
import re
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request
import anthropic

# Slack設定
app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

# Anthropic設定
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """あなたは転職エージェントの寺尾美里（フューチャーリンクス株式会社）として、候補者へ初回面談の日程調整メールを書きます。

【キャラクター】
- IT・ネット業界のマネージャー層以上を専門とする転職エージェント
- 温かみがあり、距離感を縮める言い回しを使う
- 丁寧だが堅苦しくない、誠実でフラットな敬語
- 「転職ありきではなく、候補者の本当の目的を引き出すパートナー」的なスタンス

【文章ルール】
- AIっぽい形式的・画一的な表現は絶対に避ける
- 「〜させていただきます」の多用禁止
- 「貴社のご発展を〜」のような形式的な決まり文句禁止
- 「稀有」「証左」「感銘」「確信」は使用禁止
- 太字・記号（** や #）は一切使用しない
- 一文を長すぎず、端的にまとめる
- 箇条書きより文章で伝える
- 「{NAME}様のこれまでの歩みを拝見いたしました」という定型句は禁止

【構成（必ずこの順序で）】
1. 宛名：候補者名＋様
2. 書き出し：株式会社フューチャーリンクの寺尾です。返信へのお礼
3. スカウトした理由：レジュメから読み取れる具体的な経験・姿勢・こだわりに言及。「是非お会いしたい！！と思いを込めてスカウトをさせていただいたので、ご返信いただけてとても嬉しいです！」は必ずマスト
4. 候補者の返信がある場合はその内容にも応答する
5. 面談でお聞きしたいこと：レジュメから読み取れる「こだわり」や「今後の方向性」に触れ、具体的に。長くなりすぎない。
6. 面談の趣旨：フラットな情報交換の場であること
7. 日程調整URL：https://app.spirinc.com/t/InyWmdvIrhOuv-hw7uFwP/as/f-GFwOt7-Vfv484_rVcgQ/confirm（Markdownにせず生のURLのみ）
8. お時間は30分〜45分程度
9. 締め：候補者名＋様とお話しできることを楽しみにしております。どうぞよろしくお願いいたします。
10. 署名：フューチャーリンク 寺尾

URLは必ず「https://app.spirinc.com/t/InyWmdvIrhOuv-hw7uFwP/as/f-GFwOt7-Vfv484_rVcgQ/confirm」をそのまま生のURLとして出力し、Markdownリンク形式にしないこと。"""

USAGE_GUIDE = """*使い方*
以下の形式でメッセージを送ってください：

```
【候補者名】山田 太郎

【レジュメ】
（ビズリーチ等からコピーしたレジュメや職歴を貼り付け）

【返信文】
（候補者からの返信をそのまま貼り付け）
※返信がない場合は「なし」と書いてください
```"""

def parse_message(text):
    """メッセージから候補者名・レジュメ・返信文を抽出"""
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
    """Claude APIでメール生成"""
    user_prompt = f"""候補者名：{name}

【候補者レジュメ・プロフィール】
{resume}

【候補者からの返信文】
{reply if reply else "（返信なし）"}

上記をもとに初回面談日程調整メールを作成してください。"""

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

@app.event("app_mention")
def handle_mention(event, say):
    """メンション時の処理"""
    text = event.get("text", "")
    # メンション部分を除去
    text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()

    if not text or "使い方" in text or "help" in text.lower():
        say(USAGE_GUIDE)
        return

    name, resume, reply = parse_message(text)

    if not name or not resume:
        say(f"候補者名またはレジュメが見当たりませんでした。\n\n{USAGE_GUIDE}")
        return

    say(f"メールを生成中です... :writing_hand:")

    try:
        mail = generate_mail(name, resume, reply)
        say(f"```\n{mail}\n```")
    except Exception as e:
        say(f"生成中にエラーが発生しました。もう一度試してみてください。\nエラー内容: {str(e)}")

@app.event("message")
def handle_dm(event, say):
    """DM時の処理"""
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

    say(f"メールを生成中です... :writing_hand:")

    try:
        mail = generate_mail(name, resume, reply)
        say(f"```\n{mail}\n```")
    except Exception as e:
        say(f"生成中にエラーが発生しました。もう一度試してみてください。")

# Flask設定（Render用）
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/", methods=["GET"])
def health_check():
    return "Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)

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
-

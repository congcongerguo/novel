# -*- coding: utf-8 -*-
"""ep01 短剧视频 · MiniMax H3 多参图生视频（25 镜）· v2.0 官方语法版

════════════════════════════════════════════════════════════════════════
v2.0 修复（2026-09-12 · 作者指出三个问题后的重写）
────────────────────────────────────────────────────────────────────────
v1.0（错误版，已备份为 `_deprecated_gen_ep01_h3_错误版.py`）丢了 H3 三段关键语法，
导致三个可观察的问题，逐条对应：

  问题①「视频和首图没关系」
    原因：场景 `<Subject N>` 描述没有锚定到 `<Picture 1>`
    修法：每镜的场景/道具必须写 `... in <Picture 1>: ...`（官方写法见
          spec/visual/shotlists/*.json）

  问题②「语言不对，不是英文就是乱码」
    原因：完全没有对白标记 `<d>[Chinese] 台词。</d>`，还在有台词的镜上写死
          `No dialogue.`；并且声景里出现了 `her voice carrying on the air` 这类
          “触发词”，模型没有语言约束就自己编语音
    修法：① 对白一律用 `<d>[Chinese] …</d>` 内联（并标说话人 (S1)/(S2)）
          ② 声景里**禁止出现 voice / says / speaking / talking / murmur of words**
             之类触发词，除非确实有 `<d>` 对白
          ③ 无对白的镜写 `No dialogue.` 且描述里不出现任何“说话”动作

  问题③「同一场景轴线不对」
    原因：detailed_description 里只写了套话
          `framed tall so the subject stacks vertically`，没有机位与朝向约束
    修法：抽出 AXIS_* 常量（同场戏共用），明确机位、朝向、画面分区
          —— 尤其配给点必须与首帧一致的「侧后 3/4、面向画面右侧屏幕、不看镜头」

════════════════════════════════════════════════════════════════════════
旁白（V.O.）策略：**不进 H3**
  V.O. 需要“心里的话”（不张嘴、音色可控），H3 处理不好，且会抢对白的音轨。
  6 句 V.O. 一律**后期单独配音**，对应镜写 `No dialogue.`
  详见 spec/visual/ep01-配音剪辑台本.md
════════════════════════════════════════════════════════════════════════

用法：
  python gen_ep01_h3.py s01
  python gen_ep01_h3.py s04 s07        # 抽检
  python gen_ep01_h3.py all
输出：releases/2026-09-12_ep01_成片包/03_镜头视频/<镜号>_<名>.mp4
"""
import json, os, sys, time
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HOST = "http://127.0.0.1:8188"

# 连接池 + 自动重试（2026-09-12 事故修复）
# 根因：urllib 每次新建连接 → Windows TIME_WAIT 堆积 → 动态端口耗尽
S = requests.Session()
_RETRY = Retry(total=6, backoff_factor=1.5,
               status_forcelist=[500, 502, 503, 504],
               allowed_methods=frozenset(["GET", "POST"]))
S.mount("http://", HTTPAdapter(max_retries=_RETRY, pool_connections=4, pool_maxsize=4))

ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
FRAME_DIR = P.EP01_FRAMES
OUT_DIR = P.EP01_VIDEOS
CARD = ROOT / "input" / "juese" / "luyuan" / "luyuan.png"            # <Picture 2>
FRONT = ROOT / "input" / "juese" / "luyuan" / "三视图" / "front.png"  # <Picture 3>

# ─────────────────────────── 常量 ───────────────────────────

CAM_HEAD = ("The target video is a photorealistic documentary-style vertical 9:16 shot "
            "with handheld micro-shake, shallow depth of field and floating dust in the light")

# 主角定义（<Subject 1>）· 与定妆照一致
LY = ("<Subject 1> is the lean 30-year-old Chinese man defined by <Picture 2> (character sheet) "
      "and <Picture 3> (full-body front view): lean wiry build, short messy black hair, old "
      "black-frame glasses with a scratched left lens and a taped temple, a washed-out plaid "
      "shirt with a frayed collar, dark work pants, and rough hands with oil-grey under the "
      "short nails.")
LY_PART = ("<Subject 1> is the lean 30-year-old Chinese man defined by <Picture 2> (character "
           "sheet) and <Picture 3> (full-body front view): a washed-out plaid shirt with a "
           "frayed collar, rough hands with oil-grey under the short nails.")

# ── 机位 / 轴线常量（同场戏共用，防朝向乱跳） ──
AXIS_ROOM = ("warm dawn light coming through the plastic sheet, the plaster wall reading warm "
             "and bone-white; the camera is a low handheld frame inside the small room, the "
             "socket and the hand stacking vertically in the narrow frame")
AXIS_ROOM_WIDE = ("warm dawn side light through the plastic sheet; the crouched figure sits in "
                  "the lower half of the tall frame with the window light falling from the "
                  "upper left")
AXIS_STREET = ("hard late-morning side light; he stands in the lower two thirds of the tall "
               "frame with the street and the shopfronts stacking upward behind him, and the "
               "camera never moves away from his position on the pavement")
AXIS_STALL = ("hard afternoon side light raking across the metal parts; the two men stand in "
              "the lower two thirds of the tall frame facing each other three-quarters on - he "
              "at the left, the stallholder at the right - and neither of them ever faces the lens")
AXIS_QUEUE = ("neutral institutional daylight with the skin kept warm; the queue is stacked "
              "from the bottom of the tall frame upward into the building entrance and never "
              "spreads sideways; the camera is locked off on his part of the line")
# ⚠️ 配给点内景：必须与已定稿首帧同一轴线（侧后 3/4、面向画面右侧的屏幕、不看镜头）
AXIS_WINDOW = ("warm institutional interior light with the skin kept warm, the screen glowing "
               "pale and bright; strong three-quarter back view - he stands side-on at the "
               "counter with the pale screen on the right of frame, he NEVER turns toward the "
               "lens, and the screen light falls across the side of his face and the edge of "
               "his glasses")
AXIS_JUNK = ("warm afternoon light through a plastic-sheet awning that cuts the sky at the top "
             "of the frame; the rusted machine sits low in the lower half and the pile of scrap "
             "heaps up around it, and the handheld camera stays on his eye level")
AXIS_DUSK = ("golden-hour backlight from the alley mouth with long shadows running down the "
             "tall frame; the two men squat at the same level in the lower third of the frame, "
             "facing each other three-quarters on, and neither faces the lens")
AXIS_NIGHT = ("night in the junk lot under a sodium street lamp whose warm orange light "
              "reaches the whole alley; the rusted machine sits low in the frame and the "
              "camera is a handheld night frame on his eye level; shadows stay warm brown and "
              "readable, never crushed to black")

# 镜号 → 首帧文件名
FRAME_FILE = {
    "s01": "A3_充电头怼三孔圆口.png",
    "s02": "s02_蹲地碾铜脚.png",
    "s03": "s03_被当成噪音.png",
    "s04": "s04_让你的模型来问.png",
    "s05": "s05_你没登记吧.png",
    "s06": "s06_配给点长队.png",
    "s07": "s07_核验失败.png",
    "s08": "s08_预约死循环.png",
    "s09": "s09_方案与选择.png",
    "s10": "s10_哪部分经历.png",
    "s11": "s11_把家卖了.png",
    "s12": "s12_街边逆光.png",
    "s13": "A1_废品收购站场景.png",
    "s14": "s14_无所事事坐着.png",
    "s15": "A2_锈迹斑斑的旧设备.png",
    "s16": "s16_拨了一下.png",
    "s17": "s17_屏幕光映脸.png",
    "s18": "s18_怎么修好的.png",
    "s19": "s19_塞干粮与硬币.png",
    "s20": "s20_别往新城区说.png",
    "s21": "s21_三种人吃东西.png",
    "s22": "s22_摸到兜里那个.png",
    "s23": "s23_插上电源口.png",
    "s24": "A4_手机屏幕2%.png",
    "s25": "s25_他抬起头.png",
}

# ─────────────────────────── 25 镜定义 ───────────────────────────
# 每镜：name / frames / subjects / first / summary / retention / camera / beats / close / sound_text
SHOTS = {}

SHOTS["s01"] = dict(
    name="插不进插座", frames=141,
    subjects=[
        LY_PART,
        "<Subject 2> is the worn interior wall and the round white three-hole socket in <Picture 1>, "
        "inside the abandoned room: cracked plaster, a window covered with plastic sheeting that "
        "bulges in the wind, dust hanging in the air.",
    ],
    first="an extreme close-up of a rough hand pressing an old grey two-pin charger against the "
          "round three-hole socket, its two flat prongs misaligned with the round holes.",
    summary="<Subject 1>'s hand tries to force the old two-pin charger into the round socket of "
            "<Subject 2>, fails twice, and finally hangs in mid-air between retries; only his hand "
            "and shirt cuff appear.",
    retention=[
        "<Subject 1> (appears in [Shot 1], hand and cuff only): partially_preserved - only his "
        "rough hand, wrist and the frayed plaid cuff are visible; his face never enters the frame.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the cracked plaster, the round "
        "three-hole socket and the plastic-sheet window are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_ROOM,
    beats=[
        "From 00:00.3 to 00:01.6, the hand presses the charger flat against the socket; the two "
        "flat prongs catch the ceramic rim, scrape once, and slip aside.",
        "From 00:01.6 to 00:03.0, the wrist rotates to try another angle and presses again; the "
        "prongs slip off a second time, and the thumb rubs slowly over the polished copper prongs.",
        "From 00:03.0 to 00:05.9, the hand pulls the charger a few centimetres away from the wall "
        "and holds it in mid-air; the handheld camera dips slightly and settles on the gap between "
        "the plug and the round holes, then holds still.",
    ],
    close="No dialogue.", sound="",
    sound_text="Quiet room tone; a faint low electrical hum that never stops; wind pressing the "
               "plastic sheet; a dry ceramic scrape each time the prongs slip; distant traffic "
               "far below.",
)

SHOTS["s02"] = dict(
    name="碾铜脚", frames=175,
    subjects=[
        LY,
        "<Subject 2> is the bare abandoned room in <Picture 1>: a heap of flattened cardboard "
        "boxes in place of a bed, a plastic sheet nailed over the window frame, warm dawn light "
        "cutting in across the floor.",
    ],
    first="a medium shot of <Subject 1> crouched on the floor below the wall socket, the small "
          "charger in one hand with his thumb resting on its worn copper prongs, head lowered.",
    summary="<Subject 1> stays crouched under the socket, rubs the worn copper prongs with his "
            "thumb, glances at the dark phone in his other hand, then pulls one flattened "
            "cardboard box out of the pile and lies down on it with its handwritten edge facing up.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses with the "
        "scratched left lens, plaid shirt and crouched posture are retained from <Picture 2> and "
        "<Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the cardboard heap, the "
        "plastic-sheet window and the slanting dawn light are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_ROOM_WIDE,
    beats=[
        "From 00:00.3 to 00:02.2, his thumb rubs back and forth over the copper prongs, small and "
        "repetitive, the metal catching a brief warm glint.",
        "From 00:02.2 to 00:03.6, he lifts the dark phone in his other hand, looks at the black "
        "screen for a beat, and lowers it again without pressing anything.",
        "From 00:03.6 to 00:05.6, he pulls a flattened cardboard box out of the pile with one "
        "hand and turns it over; faded printed characters cover one face and a line of handwriting "
        "runs along its edge.",
        "From 00:05.6 to 00:07.3, he sets the box down with the handwritten edge facing up, lies "
        "back onto the pile, and stays still; the light through the plastic sheet brightens "
        "slightly and the frame holds.",
    ],
    close="No dialogue.",
    sound_text="Quiet room tone; the plastic sheet cracking softly as the wind presses it; "
               "cardboard scraping over the floor; the same faint low electrical hum that never "
               "stops.",
)

SHOTS["s03"] = dict(
    name="被当成噪音", frames=175,
    subjects=[
        LY,
        "<Subject 2> is the old-town street in <Picture 1>: cracked concrete, old shopfronts with "
        "peeling paint, hand-painted signs mixed with new panels, hard late-morning light.",
        "<Subject 3> is the stream of passers-by in <Picture 1>: each one wearing an invisible "
        "in-ear device, none of them wearing any wire, earbud cord or headband, and none of them "
        "ever looking at <Subject 1>.",
    ],
    first="a medium shot of <Subject 1> standing still in the middle of the old-town street with "
          "pedestrians crossing on both sides of him and no one's eyes on him.",
    summary="<Subject 1> stands still in the middle of <Subject 2> while <Subject 3> crosses past "
            "him on both sides without a glance; one figure cuts across the close foreground, and "
            "when they clear he is standing in exactly the same place.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "stillness are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the cracked concrete, the "
        "shopfronts and the hard side light are retained exactly as in <Picture 1>.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - every passer-by stays in soft "
        "focus with an invisible in-ear device and never turns toward <Subject 1>.",
    ],
    camera=AXIS_STREET,
    beats=[
        "From 00:00.3 to 00:02.4, he stands still with his chin slightly raised while two streams "
        "of people pass on both sides; a shoulder comes close enough to brush him and its owner "
        "walks on without turning.",
        "From 00:02.4 to 00:04.4, a passer-by crosses the close foreground with light motion blur "
        "and blocks half the frame for a beat; when they clear, he is standing in exactly the same "
        "place.",
        "From 00:04.4 to 00:07.3, he turns his head a few degrees to follow the crowd, then lowers "
        "his chin; his hand closes around the small charger in his pocket and the crowd keeps "
        "moving around him.",
    ],
    close="No dialogue.",
    sound_text="A busy old-town street bed of footsteps and hand carts; the shuffle of a crowd "
               "passing close to camera; a distant low electrical hum underneath everything.",
)

SHOTS["s04"] = dict(
    name="让你的模型来问", frames=209,
    subjects=[
        "<Subject 1> is the lean 30-year-old Chinese man defined by <Picture 2> (character sheet) "
        "and <Picture 3> (full-body front view): a washed-out plaid shirt with a frayed collar, "
        "old black-frame glasses; seen over his own shoulder, mostly from behind.",
        "<Subject 2> is the middle-aged Chinese woman in <Picture 1>: dark hair tied back, a plain "
        "dark jacket, a cloth bag of vegetables on her arm, and an invisible in-ear device - there "
        "is no wire, cord or headband anywhere on her.",
        "<Subject 3> is the old-town street corner in <Picture 1>: peeling shopfronts and cracked "
        "pavement in warm late-morning light.",
    ],
    first="a medium shot over <Subject 1>'s right shoulder: <Subject 2> facing him with her head "
          "down, and his shoulder and the back of his head filling the right edge of frame in "
          "soft focus.",
    summary="<Subject 1>, with only his shoulder and the back of his head in frame, asks "
            "<Subject 2> a question; she answers without lifting her head and tells him to let his "
            "model do the asking, then walks off past the camera.",
    retention=[
        "<Subject 1> (appears in [Shot 1], shoulder and back of head only): partially_preserved - "
        "his shoulder, the frayed plaid collar and the edge of his glasses appear in soft focus; "
        "his full face stays off-frame.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - her tied-back hair, plain jacket, "
        "cloth vegetable bag and invisible in-ear device are retained exactly as in <Picture 1>.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the street corner and the shopfront "
        "behind her are retained exactly as in <Picture 1>.",
    ],
    camera=("warm late-morning light over the shoulder; the camera holds behind his shoulder so "
            "that <Subject 2> sits in the upper half of the tall frame turned three-quarters "
            "toward him, while he stays a soft blurred shoulder at the right edge and never faces "
            "the lens"),
    beats=[
        "From 00:00.4 to 00:01.6, <Subject 1> (S1) speaks toward the woman in a plain tired male "
        "voice, <d>[Chinese] 请问——</d>",
        "From 00:01.6 to 00:03.6, <Subject 2> (S2) answers without lifting her head, her tone flat "
        "and unhurried, <d>[Chinese] 让你的模型来问。</d>",
        "From 00:03.6 to 00:05.2, she glances up at him for a single beat - she notices his old "
        "glasses - then drops her eyes again and says nothing more.",
        "From 00:05.2 to 00:08.7, she shifts the vegetable bag on her arm and walks off past the "
        "camera; the shoulder at the right edge shifts slightly but he does not follow her, and "
        "the camera holds on the space she has left.",
    ],
    close="No other dialogue.",
    sound_text="Street bed of footsteps and distant carts; the soft scuff of a cloth bag against "
               "an arm; no music.",
)

SHOTS["s05"] = dict(
    name="你没登记吧", frames=260,
    subjects=[
        LY,
        "<Subject 2> is the middle-aged Chinese stallholder in <Picture 1>: a worn dark jacket, a "
        "rag in one hand, wiping a pile of old screws; he is a separate character, not <Subject 1>.",
        "<Subject 3> is the old-parts stall in <Picture 1>: a trestle table covered with old "
        "screws, hinges, small iron boxes and salvaged parts in hard afternoon sunlight.",
    ],
    first="a medium two-shot at the stall: <Subject 1> standing at the left of frame, and "
          "<Subject 2> looking up from the pile of screws he is wiping.",
    summary="<Subject 1> asks how to register; <Subject 2> looks him over, tells him he is not "
            "registered and sends him to the ration point, then goes back to his screws.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "the small charger in his hand are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - his worn jacket, the rag in his hand "
        "and the way he wipes the screws are retained exactly as in <Picture 1>.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the trestle table, the screws and "
        "the iron boxes are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_STALL,
    beats=[
        "From 00:00.4 to 00:02.2, <Subject 2> (S2) looks up from the screws, runs his eyes over "
        "<Subject 1>'s shirt and the charger in his hand, and speaks while still wiping, "
        "<d>[Chinese] 你没登记吧。</d>",
        "From 00:02.4 to 00:03.6, <Subject 1> (S1) answers in a plain tired male voice, "
        "<d>[Chinese] ……怎么登记？</d>",
        "From 00:03.6 to 00:08.0, <Subject 2> (S2) keeps wiping the screws and talks without "
        "looking up, <d>[Chinese] 去配给点。无证人员有救助配额。</d>",
        "From 00:08.0 to 00:10.8, he glances up once more and jerks his chin down the street, "
        "<d>[Chinese] 先去领上。不然你连今天都过不去。</d> then drops back to the screws; "
        "<Subject 1> stands a beat longer and turns away without replying.",
    ],
    close="No other dialogue.",
    sound_text="Street bed of distant traffic; a rag rubbing against metal; screws shifting in an "
               "iron box; no music.",
)

SHOTS["s06"] = dict(
    name="配给点长队", frames=175,
    subjects=[
        LY,
        "<Subject 2> is the ration-point queue in <Picture 1>: a long quiet column of people "
        "standing along the pale institutional wall, every head bent toward a wrist or an ear, "
        "nobody speaking and nobody cutting in.",
        "<Subject 3> is the pale institutional counter front in <Picture 1>, with a gate panel "
        "standing beside it.",
    ],
    first="a vertical shot of the quiet queue along the pale wall, with <Subject 1> standing at "
          "the near end of the line looking down at his own bare wrist.",
    summary="the queue of <Subject 2> holds perfectly still; a man midway up the line lifts his "
            "wrist to the gate panel and walks straight past everyone without anyone reacting; "
            "<Subject 1> follows him with his eyes and then looks down at his own empty wrist.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "the small charger in his hand are retained from <Picture 2> and <Picture 3>; he stays at "
        "the near end of the line in the lower part of the tall frame.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the stillness of the column and the "
        "bent heads are retained exactly as in <Picture 1>, stacked vertically into depth.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the pale wall, the counter front and "
        "the gate panel are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_QUEUE,
    beats=[
        "From 00:00.4 to 00:02.4, nothing moves at all; the column stands shoulder to shoulder "
        "with every head down, only a faint shifting of weight breaking the stillness.",
        "From 00:02.4 to 00:04.4, a man midway up the line lifts his wrist to the gate panel; it "
        "flashes once and he walks straight past the head of the queue and inside, and not one "
        "person in the line looks up.",
        "From 00:04.4 to 00:07.3, <Subject 1> follows him with his eyes, then lowers his gaze to "
        "his own bare wrist and keeps it there; the line holds, motionless.",
    ],
    close="No dialogue.",
    sound_text="A hushed, wordless crowd of shuffling feet and slow breathing; one soft "
               "electronic chime from the gate; a low institutional hum.",
)

SHOTS["s07"] = dict(
    name="核验失败", frames=209,
    subjects=[
        LY,
        "<Subject 2> is the institutional counter screen in <Picture 1>: a pale faceless panel "
        "above the counter with lines of text scrolling upward and a flat synthesized female "
        "voice; there is no human face behind it.",
    ],
    first="a medium shot at the counter: <Subject 1> standing three-quarters away from the lens, "
          "facing the pale screen on the right of frame, its glow falling across the edge of his "
          "glasses.",
    summary="the screen of <Subject 2> finishes its verification and announces that <Subject 1> "
            "is not in the system; he answers that he came to register, and the screen simply "
            "keeps scrolling.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his plaid shirt, the edge of his "
        "glasses and the set of his shoulders are retained from <Picture 2>, <Picture 3> and "
        "<Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pale panel, the scrolling text "
        "and its glow are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_WINDOW,
    beats=[
        "From 00:00.3 to 00:04.0, the text scrolls faster and <Subject 2> (S2) announces in a "
        "flat, unhurried synthesized female voice, <d>[Chinese] 正在核验。核验失败——您不在系统内。</d>",
        "From 00:04.2 to 00:06.6, <Subject 1> (S1) does not step back; he answers in a plain tired "
        "male voice, <d>[Chinese] 我知道。所以我来登记。</d>",
        "From 00:06.6 to 00:08.7, the screen keeps scrolling without replying, its glow steady on "
        "the side of his face and glasses, and he stays where he is with one hand on the counter "
        "edge.",
    ],
    close="No other dialogue.",
    sound_text="Low institutional hum and cooling-fan noise; the hush of the queue waiting "
               "behind him; the synthesized voice with no room reflection on it.",
)

SHOTS["s08"] = dict(
    name="预约死循环", frames=260,
    subjects=[
        LY,
        "<Subject 2> is the institutional counter screen in <Picture 1>: a pale faceless panel "
        "with lines of text scrolling upward and a flat synthesized female voice.",
    ],
    first="a medium shot at the counter: <Subject 1> standing three-quarters away from the lens "
          "facing the pale screen on the right, his shoulders slightly tense.",
    summary="<Subject 1> is caught in a closed loop by <Subject 2> - registration needs an "
            "appointment, an appointment needs an identity, and he has none - and the screen ends "
            "by announcing a contradiction while the queue behind him begins to stir.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his shirt, the edge of his glasses "
        "and the tension in his shoulders are retained from <Picture 2>, <Picture 3> and "
        "<Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pale panel and its scrolling "
        "text are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_WINDOW,
    beats=[
        "From 00:00.4 to 00:02.0, <Subject 2> (S2) says in the same flat synthesized female voice, "
        "<d>[Chinese] 登记需要预约。</d>",
        "From 00:02.2 to 00:03.2, <Subject 1> (S1) answers without missing a beat, in a plain "
        "male voice, <d>[Chinese] 那我预约。</d>",
        "From 00:03.4 to 00:05.0, <Subject 2> (S2) replies in exactly the same flat tone, "
        "<d>[Chinese] 预约需要身份。</d>",
        "From 00:05.2 to 00:06.4, <Subject 1> (S1) says, quieter this time, <d>[Chinese] 那我没身份。</d>",
        "From 00:06.6 to 00:10.8, <Subject 2> (S2) states flatly, <d>[Chinese] 检测到矛盾。</d> then "
        "the panel scrolls on in silence; <Subject 1> stands perfectly still with one hand on the "
        "counter, and behind him somebody coughs and shifts their weight.",
    ],
    close="No other dialogue.",
    sound_text="Low institutional hum and cooling-fan noise; behind him a queue beginning to "
               "stir - a cough, shoes scuffing, a sigh.",
)

SHOTS["s09"] = dict(
    name="方案A与B", frames=260,
    subjects=[
        LY,
        "<Subject 2> is the institutional counter screen in <Picture 1>: a pale faceless panel "
        "with lines of text scrolling upward and a flat synthesized female voice.",
    ],
    first="a medium shot at the counter: <Subject 1> standing three-quarters away from the lens "
          "facing the pale screen on the right, its glow rising across his cheekbone.",
    summary="<Subject 2> lays out two options for <Subject 1> - a temporary identity with a long "
            "review period, or signing away his experience with immediate effect - and he asks "
            "what the second option is.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his shirt, the edge of his glasses "
        "and his stillness are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pale panel and its scrolling "
        "text are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_WINDOW,
    beats=[
        "From 00:00.4 to 00:07.6, <Subject 2> (S2) speaks in the flat synthesized female voice, "
        "unhurried and perfectly polite, <d>[Chinese] 建议方案 A：申请临时身份，审核周期四至六周。"
        "方案 B：签署样本代理协议，即时生效，效率最优。</d> and the text scrolls on unchanged "
        "throughout.",
        "From 00:07.8 to 00:10.8, <Subject 1> (S1) asks in a plain male voice, "
        "<d>[Chinese] 方案 B 是什么。</d> and the screen keeps scrolling without pausing.",
    ],
    close="No other dialogue.",
    sound_text="Low institutional hum and cooling-fan noise; the queue behind him shifting; the "
               "synthesized voice with no room reflection on it.",
)

SHOTS["s10"] = dict(
    name="哪部分经历", frames=209,
    subjects=[
        LY,
        "<Subject 2> is the institutional counter screen in <Picture 1>: a pale faceless panel "
        "with lines of text scrolling upward and a flat synthesized female voice.",
    ],
    first="a medium close shot at the counter three-quarters from behind: <Subject 1> has lowered "
          "his head to look at the small dark phone in his hand, with the pale screen on the right "
          "and its glow along his cheek and glasses.",
    summary="<Subject 2> explains what signing the agreement means; <Subject 1> looks down at the "
            "dark phone in his hand and asks which part of his experience they mean.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his shirt, the edge of his glasses "
        "and the small dark phone in his hand are retained from <Picture 2>, <Picture 3> and "
        "<Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pale panel and its scrolling "
        "text are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_WINDOW,
    beats=[
        "From 00:00.4 to 00:06.2, <Subject 2> (S2) explains in the same even synthesized female "
        "voice, <d>[Chinese] 将您的经历授权予模型公司，作为训练样本，即时获得配额。约 17% 的"
        "无证人员选这个。</d>",
        "From 00:06.4 to 00:08.7, <Subject 1> (S1) has already dropped his head to the small dark "
        "phone in his hand; he turns it over once without pressing anything and asks, low, "
        "<d>[Chinese] ……哪部分经历。</d>",
    ],
    close="No other dialogue.",
    sound_text="Low institutional hum and cooling-fan noise; the queue shuffling behind him; the "
               "synthesized voice with no room reflection on it.",
)

SHOTS["s11"] = dict(
    name="把家卖了", frames=311,
    subjects=[
        LY,
        "<Subject 2> is the institutional counter screen in <Picture 1>: a pale faceless panel "
        "with lines of text scrolling upward and a flat synthesized female voice.",
        "<Subject 3> is the crowd in <Picture 1> behind <Subject 1> at the counter: shoulders and "
        "arms that surge forward past him; only bodies, always faceless and blurred.",
    ],
    first="a medium close shot at the counter three-quarters from behind: <Subject 1> with his "
          "head lifted slightly toward the pale screen on the right, blurred people pressing "
          "behind him.",
    summary="<Subject 2> confirms that the agreement covers all of his experience, including what "
            "he remembers; <Subject 1> murmurs that they are asking him to sell his home, "
            "<Subject 2> answers that the system offers options and judges none, and then "
            "<Subject 3> pushes him off the counter.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his shirt, glasses, and the small "
        "dark phone in his hand are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1], voice and glow only): fully_preserved - the pale panel "
        "and its flat voice are retained exactly as in <Picture 1>.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - they stay blurred and faceless, "
        "bodies pushing through the frame.",
    ],
    camera=AXIS_WINDOW,
    beats=[
        "From 00:00.4 to 00:01.0, <Subject 2> (S2) answers in the flat synthesized female voice, "
        "<d>[Chinese] 全部。</d>",
        "From 00:01.2 to 00:03.2, <Subject 1> (S1) keeps looking at the dark phone in his hand and "
        "asks, <d>[Chinese] 包括我记得的东西。</d>",
        "From 00:03.4 to 00:05.0, <Subject 2> (S2) replies without a pause, <d>[Chinese] 记忆是"
        "经历的存储形式。</d>",
        "From 00:05.2 to 00:07.6, <Subject 1> (S1) says, very low, almost swallowed by the hum, "
        "<d>[Chinese] ……你们让我把家卖了。</d>",
        "From 00:07.8 to 00:09.4, <Subject 2> (S2) states, entirely unmoved, "
        "<d>[Chinese] 系统不评价方案，只提供方案。</d>",
        "From 00:09.4 to 00:12.9, <Subject 3> surges forward from behind; shoulders and arms push "
        "into frame, <Subject 1> is jostled sideways out of the counter position, and the handheld "
        "camera is shaken loose with him and left looking along the pale wall.",
    ],
    close="No other dialogue.",
    sound_text="The synthesized voice with no room reflection; a sudden swell of shoes and "
               "murmuring as the crowd pushes through; the institutional hum underneath it all.",
)

SHOTS["s12"] = dict(
    name="街边逆光", frames=175,
    subjects=[
        LY,
        "<Subject 2> is the street-side kerb in <Picture 1> at late afternoon: warm low backlight, "
        "a long shadow running away from camera, clear haze-free air.",
    ],
    first="a medium shot of <Subject 1> standing at the kerb looking down at the small charger in "
          "his hand, its copper prongs catching the low warm backlight.",
    summary="<Subject 1> looks down at the small charger in his palm, turns it once so the low sun "
            "moves along the copper prongs, closes his fist around it, and lifts his eyes into the "
            "light.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "hands are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the kerb, the long shadow and the "
        "low warm backlight are retained exactly as in <Picture 1>.",
    ],
    camera=("warm late-afternoon backlight rimming his outline, his head in the upper half of the "
            "tall frame and his long shadow running down the lower half; the handheld camera stays "
            "on his eye level and never crosses to the other side of him"),
    beats=[
        "From 00:00.4 to 00:02.6, the charger lies across his open palm; he turns it slightly with "
        "his thumb and watches the light travel along the copper prongs.",
        "From 00:02.6 to 00:04.8, his fingers close over it and he grips it tight, the charger "
        "disappearing into his fist.",
        "From 00:04.8 to 00:07.3, he raises his eyes into the low light off-frame; the backlight "
        "draws a bright edge along his jaw and the taped temple of his glasses, and his long "
        "shadow lies across the pavement behind him.",
    ],
    close="No dialogue.",
    sound_text="Distant traffic and a faint wind; the soft creak of fabric as his fingers close; "
               "no music.",
)

SHOTS["s13"] = dict(
    name="废品收购站", frames=124,
    subjects=[
        "<Subject 2> is the scrap lot in <Picture 1>: heaps of stripped machine casings, flattened "
        "sheet metal, a half-dismantled refrigerator and a stack of unmarked monitors piled into a "
        "small hill under a plastic-sheet awning.",
    ],
    first="a wide vertical shot of the scrap lot alley corner: heaps of stripped casings, sheet "
          "metal and unmarked monitors piled into a hill under a plastic-sheet awning, with the "
          "alley mouth bright at the top of frame.",
    summary="an empty scrap-lot corner holds still in the warm afternoon light of <Subject 2>; "
            "the yard is deserted and the shot stays on the pile - nothing but drifting dust, the "
            "awning moving in the wind, and bare metal catching the light.",
    retention=[
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pile of casings, sheet metal, "
        "the half-dismantled refrigerator and the plastic awning are retained exactly as in "
        "<Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.3 to 00:02.1, dust drifts through the light and settles; the plastic awning "
        "lifts once in the wind and falls back; one bare metal edge catches the warm light and "
        "loses it.",
        "From 00:02.1 to 00:03.6, the shaft of light through the torn awning shifts a little as "
        "the sheet moves; a few loose flakes of rust turn over on the ground below it.",
        "From 00:03.6 to 00:05.1, the yard goes still again and the handheld camera settles "
        "almost imperceptibly; the pile keeps the light and the frame holds on it without cutting "
        "anywhere.",
    ],
    close="No dialogue.",
    sound_text="A quiet yard of distant traffic and wind moving loose sheet metal; the plastic "
               "awning flapping slowly overhead; the faint low electrical hum that never stops.",
)

SHOTS["s14"] = dict(
    name="无所事事", frames=260,
    subjects=[
        LY,
        "<Subject 2> is the scrap lot in <Picture 1>: heaps of stripped casings and sheet metal "
        "piled into a small hill, with a plastic-sheet awning overhead torn open in one place.",
    ],
    first="a medium shot of <Subject 1> sitting on the ground beside the scrap pile, back against "
          "the wall, one knee up, both hands resting on it, doing nothing at all.",
    summary="<Subject 1> sits on the ground beside <Subject 2> doing nothing; a shaft of light "
            "through the tear in the awning falls on his shoe, a fly circles, and he rubs the toe "
            "of his shoe against the ground once; then his idle hand drifts to the rust on the "
            "machine beside him.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "the way he sits are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the pile, the torn awning and the "
        "warm afternoon light are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.4 to 00:04.2, he does not move; he sits with both hands on his raised knee, "
        "looking at the ground in front of him, and the only movement in frame is dust in a shaft "
        "of light falling through the tear in the awning.",
        "From 00:04.2 to 00:06.4, he rubs the toe of his shoe against the ground once, knocking a "
        "little dust off, and settles back; a fly crosses the frame and drifts away.",
        "From 00:06.4 to 00:10.8, his idle hand lifts off his knee, reaches sideways without "
        "looking, and picks at a flake of rust on the machine beside him; the flake comes loose "
        "and falls, and his fingers move across the bare metal underneath it. His face never "
        "changes and he never looks at what his hand is doing.",
    ],
    close="No dialogue.",
    sound_text="A very quiet yard; the plastic awning moving slowly in the wind; one fly crossing "
               "close to the microphone; a distant low electrical hum that never stops; no music.",
)

SHOTS["s15"] = dict(
    name="旧设备", frames=209,
    subjects=[
        "<Subject 1> is the lean 30-year-old Chinese man defined by <Picture 2> and <Picture 3>: "
        "a washed-out plaid shirt, rough hands with oil-grey under the nails.",
        "<Subject 2> is the rusted machine in <Picture 1>: half a refrigerator tall, rusted past "
        "any original colour, its flaking shell giving way to a flat painted panel underneath.",
    ],
    first="a medium shot of <Subject 1>'s hands working at a flaking patch of rust on the side of "
          "the rusted machine, the panel underneath just showing through.",
    summary="<Subject 1> picks the flaking rust off the side of <Subject 2> in small pieces, "
            "revealing a flat painted panel underneath, and stops to look at it.",
    retention=[
        "<Subject 1> (appears in [Shot 1], hands and shoulders): partially_preserved - his hands, "
        "plaid sleeves and the edge of his glasses are in frame; he stays bowed over the machine.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the rusted shell, the flaking patch "
        "and the painted panel showing through are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.4 to 00:02.8, his thumb works at the edge of a flaking patch of rust; one "
        "flake comes away, then another, and both drop to the ground.",
        "From 00:02.8 to 00:05.4, he works across a wider area with two fingers, and a flat "
        "painted panel is gradually uncovered under the rust; he brushes the loose flakes aside "
        "with the back of his hand.",
        "From 00:05.4 to 00:08.7, his hand stops moving; he bows lower and looks at the bare panel "
        "and the small dusty switch sitting on it, and stays there without touching anything else.",
    ],
    close="No dialogue.",
    sound_text="Dry rust gritting and falling; the wind in the plastic awning above; the "
               "background hum of the yard.",
)

SHOTS["s16"] = dict(
    name="拨了一下", frames=192,
    subjects=[
        "<Subject 1> is the lean 30-year-old Chinese man defined by <Picture 2> and <Picture 3>: "
        "a washed-out plaid shirt, rough hand with oil-grey under the nails.",
        "<Subject 2> is the small dusty power-mode lever on the uncovered panel of the rusted "
        "machine in <Picture 1>, sitting in the standby position.",
    ],
    first="a close shot of <Subject 1>'s hand resting beside the small dusty power-mode lever on "
          "the uncovered machine panel, the lever still in the standby position.",
    summary="<Subject 1>'s hand lifts the small lever of <Subject 2> a single step; after a beat "
            "the machine answers with one deep note and a panel of light comes up, and he does not "
            "move.",
    retention=[
        "<Subject 1> (appears in [Shot 1], hand and shoulder): partially_preserved - his hand, "
        "frayed plaid sleeve and the edge of his glasses are in frame; his face stays mostly out "
        "of the shot.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the panel, the dusty lever and the "
        "position of the lever are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.4 to 00:02.0, his fingers rest beside the lever without moving, the dust on "
        "the panel undisturbed.",
        "From 00:02.0 to 00:03.2, he hooks one fingertip under the lever and lifts it a single "
        "step, with one small dry click; he does not touch anything else.",
        "From 00:03.2 to 00:08.0, after a beat the machine answers - one deep low note from inside "
        "the casing, a relay knocking over, and a flat panel of old light coming up on the machine "
        "face; he pulls his hand back an inch and stays bowed there, watching it, and the light "
        "from the panel holds steady on his sleeve.",
    ],
    close="No dialogue.",
    sound_text="One small dry click of the lever; a deep low note from inside the casing; a relay "
               "knocking over; then a soft electrical hum that settles in and stays.",
)

SHOTS["s17"] = dict(
    name="屏幕光映脸", frames=209,
    subjects=[
        LY,
        "<Subject 2> is the lit panel of the rusted machine in <Picture 1>, showing an old "
        "interface with old lettering and old icons above the uncovered switch.",
    ],
    first="a medium close shot of <Subject 1> crouched in front of the lit machine, the old "
          "interfaces's light washing over his face and glasses as he stares at it.",
    summary="<Subject 1> crouches still in front of the lit panel of <Subject 2> and reads the "
            "old interface; he leans a little closer, and then looks down at the dark phone in his "
            "own pocket.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses with the scratched "
        "left lens and plaid shirt are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the lit panel, its old lettering and "
        "old icons are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.4 to 00:03.4, he stays perfectly still, crouched in front of the lit panel, "
        "and the light of the old interface sits on his face and flares along both lenses of his "
        "glasses and the taped temple.",
        "From 00:03.4 to 00:06.0, he leans perhaps ten centimetres closer, reading the old "
        "lettering, and one hand comes up to rest on the rusted casing beside the panel.",
        "From 00:06.0 to 00:08.7, he straightens a little and his eyes drop away from the panel to "
        "the pocket of his work trousers, where the shape of the small charger sits under the "
        "cloth; he stays there, and the panel light holds on his face.",
    ],
    close="No dialogue.",
    sound_text="A steady soft electrical hum from the lit machine; the plastic awning moving in "
               "the wind; the yard quiet behind him.",
)

SHOTS["s18"] = dict(
    name="怎么修好的", frames=294,
    subjects=[
        LY,
        "<Subject 2> is the thin elderly Chinese man in <Picture 1>: seventy-odd, thin and "
        "slightly stooped, a grey cloth jacket, a woven bag in one hand, standing two steps away "
        "and keeping his distance.",
        "<Subject 3> is the scrap lot in <Picture 1> with the rusted machine and its lit panel "
        "between the two men.",
    ],
    first="a medium two-shot at golden hour: <Subject 1> crouched beside the rusted machine with "
          "its panel lit, and <Subject 2> standing two steps away with a woven bag, not coming "
          "closer.",
    summary="<Subject 2> asks in a low voice how <Subject 1> fixed it; <Subject 1> answers from "
            "where he crouches that he did not fix it - it was never broken, only left in standby "
            "behind one switch - then closes the panel and pushes himself up on stiff legs.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his crouched posture, plaid shirt "
        "and glasses are retained from <Picture 2>, <Picture 3> and <Picture 1>; he speaks without "
        "straightening up.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - his thin stooped frame, grey jacket "
        "and the woven bag are retained exactly as in <Picture 1>; he stays two steps away and "
        "never faces the lens directly.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the rusted machine and its lit panel "
        "are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.5 to 00:02.4, <Subject 2> (S2) asks in a low rough elderly voice, "
        "<d>[Chinese] 你……怎么修好的。</d>",
        "From 00:02.6 to 00:05.4, <Subject 1> (S1), still looking at the machine rather than at "
        "him, answers in a plain tired male voice, <d>[Chinese] 没修好。它没坏。一个开关的事。</d>",
        "From 00:05.6 to 00:08.6, he presses the panel shut with the flat of his hand and it "
        "clicks into place, the old light disappearing behind it.",
        "From 00:08.6 to 00:12.3, he pushes himself up off the ground, his legs stiff, and has to "
        "put a hand on the rusted casing to steady himself; <Subject 2> watches him from two steps "
        "away and neither of them says anything.",
    ],
    close="No other dialogue.",
    sound_text="The panel clicking shut; the machine's hum dropping to nothing; cloth and dry "
               "ground as he gets up; the plastic awning overhead; distant evening traffic.",
)

SHOTS["s19"] = dict(
    name="塞干粮硬币", frames=294,
    subjects=[
        "<Subject 1> is the open palm of the lean 30-year-old Chinese man defined by <Picture 2> "
        "and <Picture 3>: rough-skinned with oil-grey under the short nails.",
        "<Subject 2> is the weathered hand of the elderly man in <Picture 1> pressing a small "
        "cloth bundle of dry rations and two worn coins down into that palm.",
    ],
    first="an extreme close-up of two hands: the weathered hand of <Subject 2> pressing a small "
          "cloth bundle of dry rations and two worn coins into the open palm of <Subject 1>.",
    summary="<Subject 2> presses dry rations and two coins into the palm of <Subject 1> and "
            "withdraws upward out of frame, leaving them lying in the open hand.",
    retention=[
        "<Subject 1> (appears in [Shot 1], hand only): fully_preserved - the rough young hand with "
        "oil-grey nails is retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1], hand only): fully_preserved - the weathered elderly "
        "hand, the cloth bundle and the two worn coins are retained exactly as in <Picture 1>.",
    ],
    camera=("warm golden light on the two hands with very shallow depth of field; the hands fill "
            "the middle of the tall frame with the scrap lot blurred above and below, and the "
            "camera stays tight on them"),
    beats=[
        "From 00:00.4 to 00:04.6, the weathered hand presses the small cloth bundle and the two "
        "coins down into the open palm and holds there; the bundle shifts a little under the "
        "thumb.",
        "From 00:04.8 to 00:07.4, the fingers of <Subject 2> let go and withdraw upward out of "
        "frame, leaving the rations and the two worn coins lying in the open palm.",
        "From 00:07.4 to 00:12.3, the young hand does not close; it stays open and perfectly "
        "still, and the coins settle into the lines of the palm; the golden light moves slightly "
        "across the skin.",
    ],
    close="No dialogue.",
    sound_text="Dry cloth rustling; the small metallic click of two coins settling into a palm; "
               "the plastic awning overhead; distant evening traffic; no music.",
)

SHOTS["s20"] = dict(
    name="别往新城区说", frames=294,
    subjects=[
        LY,
        "<Subject 2> is the thin elderly Chinese man in <Picture 1>: seventy-odd, thin and "
        "stooped, a grey cloth jacket, a woven bag in one hand, standing two steps away, his voice "
        "dropping lower as he speaks.",
        "<Subject 3> is the scrap lot in <Picture 1> at dusk, with the rusted machine standing "
        "silent between the two men.",
    ],
    first="a medium two-shot at dusk: <Subject 1> standing beside the silent rusted machine and "
          "<Subject 2> two steps away with his woven bag, speaking with his voice lowered.",
    summary="<Subject 2> warns <Subject 1> in a voice that keeps dropping that this should not be "
            "spoken of in the new district, because he has made something the Bureau condemned "
            "breathe again; then he picks up his bag and walks off.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses and plaid shirt "
        "are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - his stooped frame, grey jacket, "
        "woven bag and lowered posture are retained exactly as in <Picture 1>; he never faces the "
        "lens directly.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the rusted machine and the dusk "
        "light in the lot are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_JUNK,
    beats=[
        "From 00:00.5 to 00:04.0, <Subject 2> (S2) says, glancing at <Subject 1> once as he "
        "speaks, <d>[Chinese] 修得好。不过这事儿，别往新城区说。</d>",
        "From 00:04.2 to 00:05.2, <Subject 1> (S1) asks in a plain male voice, "
        "<d>[Chinese] 为什么。</d>",
        "From 00:05.4 to 00:11.0, <Subject 2> (S2) glances around the empty lot and answers in a "
        "voice that drops almost to a whisper, <d>[Chinese] 均衡局判过死的东西，你让它又喘上气了。"
        "它们不爱听这个。</d>",
        "From 00:11.0 to 00:12.3, he lifts the woven bag onto his shoulder and walks away out of "
        "frame; <Subject 1> stays where he is beside the machine and watches him go.",
    ],
    close="No other dialogue.",
    sound_text="An almost empty lot at dusk; the plastic awning; the elderly man's footsteps "
               "receding over dry ground with the woven bag creaking; distant traffic.",
)

SHOTS["s21"] = dict(
    name="三种人", frames=294,
    subjects=[
        LY,
        "<Subject 2> is the young man in <Picture 1>: about twenty, squatting at the kerb, a "
        "palm-sized box clipped at his waist with a thin tube taped across his lower belly; he is "
        "a separate character, not <Subject 1>.",
        "<Subject 3> is the kerb at dusk in <Picture 1>, between the scrap lot and the darkening "
        "street.",
    ],
    first="a low two-shot at the kerb at dusk: <Subject 1> and <Subject 2> squatting side by "
          "side at the same level, <Subject 2> looking at the dry rations in <Subject 1>'s hand.",
    summary="<Subject 2> asks about the dry rations, then taps the box at his waist and says he "
            "can get everything by plugging in, and <Subject 1> answers that he is an old man from "
            "before and old men eat; <Subject 2> tells him there are only three kinds of people in "
            "the city who still eat.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses, plaid shirt and "
        "the dry rations in his hand are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - his young face, the waist box and "
        "the thin tube taped across his belly are retained exactly as in <Picture 1>.",
        "<Subject 3> (appears in [Shot 1]): fully_preserved - the kerb and the dusk light are "
        "retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_DUSK,
    beats=[
        "From 00:00.4 to 00:01.2, <Subject 2> (S2) asks, eyeing the food in <Subject 1>'s hand, "
        "<d>[Chinese] 好吃吗。</d>",
        "From 00:01.4 to 00:02.4, <Subject 1> (S1) answers with his mouth full, "
        "<d>[Chinese] 能咽下去。</d>",
        "From 00:02.6 to 00:05.6, <Subject 2> (S2) taps the palm-sized box clipped at his waist "
        "with two fingers and says, <d>[Chinese] 一接，什么都有。何必费这个劲。</d>",
        "From 00:05.8 to 00:08.0, <Subject 1> (S1) keeps chewing and answers without turning his "
        "head, <d>[Chinese] 我是旧人。旧人靠吃饭活着。</d>",
        "From 00:08.2 to 00:12.2, <Subject 2> (S2) laughs once through his nose and looks at him "
        "sideways, <d>[Chinese] 城里只有三种人吃东西。有钱人，要死的人，不在系统里的。你是哪种。</d> "
        "and the two of them stay squatting side by side while the light goes.",
    ],
    close="No other dialogue.",
    sound_text="A quiet kerb at dusk; the small box at his waist ticking faintly; dry rations "
               "crackling; distant traffic thinning out; no music.",
)

SHOTS["s22"] = dict(
    name="摸到兜里那个", frames=209,
    subjects=[
        LY,
        "<Subject 2> is the alley in <Picture 1> at night: scrap heaps along both walls, warm "
        "orange sodium light from a lamp at the far end reaching the whole alley.",
    ],
    first="a night medium shot of <Subject 1> standing in the alley, having just taken a step, "
          "one hand pushed into his trouser pocket, his body turned slightly back the way he came.",
    summary="<Subject 1> says one word over his shoulder, takes a few steps down the night alley, "
            "then stops mid-stride with his hand in his pocket, turns his head back toward the "
            "scrap lot, and pulls the small charger out into the light.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses and plaid shirt "
        "are retained from <Picture 2> and <Picture 3>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the scrap heaps, the alley walls and "
        "the warm sodium light are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_NIGHT,
    beats=[
        "From 00:00.4 to 00:01.6, <Subject 1> (S1) answers over his shoulder in a flat male voice "
        "to someone no longer in frame, <d>[Chinese] 你猜。</d>",
        "From 00:01.8 to 00:04.2, he walks two or three steps down the alley away from camera, his "
        "shadow stretching ahead of him in the sodium light.",
        "From 00:04.2 to 00:06.6, he stops mid-stride, his hand pushing into his trouser pocket, "
        "and stands still for a beat without pulling it out.",
        "From 00:06.6 to 00:08.7, he turns his head back toward the scrap lot behind him, then "
        "draws the small grey charger out of his pocket and holds it in the lamplight, and the "
        "frame holds on him with the alley empty around him.",
    ],
    close="No other dialogue.",
    sound_text="A quiet night alley; the low buzz of the sodium lamp; his own footsteps on dry "
               "ground; the distant steady hum from the lot behind him.",
)

SHOTS["s23"] = dict(
    name="插上电源", frames=209,
    subjects=[
        LY,
        "<Subject 2> is the night scrap lot in <Picture 1>: the tall rusted machine standing among "
        "the heaps under one warm orange sodium lamp.",
    ],
    first="a night medium close shot of <Subject 1> crouched low at the side of the rusted "
          "machine, bowed and in shadow from the waist down, with the lower half of his face and "
          "the underside of his glasses just catching a faint warm light rising from below.",
    summary="<Subject 1> crouches at the side of <Subject 2> and lowers the grey charger out of "
            "sight below the frame; after a moment a small warm light comes up from below and "
            "climbs across the lower half of his face, his jaw and the underside of his glasses, "
            "and he stays bowed and still.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses and plaid shirt "
        "are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the rusted casing and its dark side "
        "surface are retained exactly as in <Picture 1>, with no opening or fitting shown.",
    ],
    camera=("night in the scrap lot under the warm orange sodium lamp, the alley around him warm "
            "brown and readable rather than crushed to black; the camera is a medium close handheld "
            "frame on his face and bow-hand, and the machine stays a dark surface filling the "
            "right of frame"),
    beats=[
        "From 00:00.4 to 00:02.6, he lowers his hand below the bottom edge of the frame, out of "
        "sight, and leans his shoulder against the dark side of the casing; nothing else moves.",
        "From 00:02.6 to 00:04.6, he reaches his chin a little lower and stays bowed; his free "
        "hand steadies him against the machine and the sodium lamp keeps a warm edge along his "
        "shoulder.",
        "From 00:04.6 to 00:08.7, a faint warm light comes up from below the frame and climbs "
        "across the lower half of his face, the line of his jaw and the underside of both lenses; "
        "his expression does not change, he does not pull back, and the small light holds steady "
        "on him.",
    ],
    close="No dialogue.",
    sound_text="A quiet night yard; the sodium lamp buzzing faintly; one small soft electronic "
               "note; the hum of the yard behind everything.",
)

SHOTS["s24"] = dict(
    name="手机2%", frames=192,
    subjects=[
        "<Subject 1> is the hand and part of the face of the lean 30-year-old Chinese man defined "
        "by <Picture 2> and <Picture 3>: rough skin with oil-grey under the short nails, old "
        "black-frame glasses.",
        "<Subject 2> is the small old phone in <Picture 1>, its screen just coming up with an old "
        "interface of old lettering and old icons, a small battery figure at the top right reading "
        "2%.",
    ],
    first="an extreme close-up in the dark: <Subject 1>'s hand holding <Subject 2> with its "
          "screen just lit, the old interface and a small battery figure showing 2% at the top "
          "right, the glow sitting on his glasses and cheekbone.",
    summary="the screen of <Subject 2> comes up in the dark in <Subject 1>'s hand and stays lit "
            "with the small battery figure showing 2%; he holds it steady and does not press "
            "anything.",
    retention=[
        "<Subject 1> (appears in [Shot 1], hand and half face): partially_preserved - the rough "
        "hand, the glasses and the lit half of his face are retained from <Picture 2>, <Picture 3> "
        "and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the old interface, the old lettering "
        "and the battery figure reading 2% are retained exactly as in <Picture 1>.",
    ],
    camera=("night, an extreme close-up with the phone screen standing as the brightest light in "
            "the frame; his face and glasses are clearly lit and readable and the shadows around "
            "them stay warm brown, never crushed to black"),
    beats=[
        "From 00:00.3 to 00:02.6, the screen of <Subject 2> is already lit; the old interface "
        "fills it and the small battery figure at the top right reads 2%; his thumb rests on the "
        "edge of the casing without pressing.",
        "From 00:02.6 to 00:05.2, the light of the screen moves slightly as his hand settles, and "
        "it slides across the lenses of his glasses and down his cheekbone; nothing on the screen "
        "changes.",
        "From 00:05.2 to 00:08.0, he goes on holding it perfectly still, the small figure still "
        "reading 2% at the top right, and the frame does not move away from the lit screen and his "
        "hand.",
    ],
    close="No dialogue.",
    sound_text="The night yard very quiet; the sodium lamp buzzing low; the faintest electronic "
               "tone from the lit screen; a single soft click from the machine beside him.",
)

SHOTS["s25"] = dict(
    name="他抬起头", frames=175,
    subjects=[
        LY,
        "<Subject 2> is the rusted machine in <Picture 1>, whose dark panel has just given one "
        "more small pulse of light in the night lot.",
    ],
    first="a night medium close shot of <Subject 1> crouched in front of the rusted machine, in "
          "the middle of lifting his head toward it, the sodium backlight along his cheek and the "
          "taped temple of his glasses.",
    summary="the panel of <Subject 2> gives one more small pulse in the dark; <Subject 1> lifts "
            "his head and looks at it, and then holds perfectly still, watching, as the light "
            "fades back out.",
    retention=[
        "<Subject 1> (appears in [Shot 1]): fully_preserved - his face, glasses with the scratched "
        "left lens and plaid shirt are retained from <Picture 2>, <Picture 3> and <Picture 1>.",
        "<Subject 2> (appears in [Shot 1]): fully_preserved - the rusted casing and the surface "
        "where the panel sits are retained exactly as in <Picture 1>.",
    ],
    camera=AXIS_NIGHT,
    beats=[
        "From 00:00.4 to 00:02.4, he finishes lifting his head and holds it there, looking up at "
        "the machine face above his own eye level; the warm sodium edge stays along his jaw and "
        "the taped temple of his glasses.",
        "From 00:02.4 to 00:04.6, the dark panel gives one more small pulse of old light; his eyes "
        "fix on it and he does not move anything else - his hands stay still on his knees.",
        "From 00:04.6 to 00:07.3, the small light fades back out, leaving only the sodium lamp on "
        "his face; he goes on looking up at the machine with no change of expression, and the "
        "frame holds on him in the dark until the end.",
    ],
    close="No dialogue.",
    sound_text="Night yard silence with the sodium lamp buzzing; one small electrical change in "
               "the machine's hum at the moment the light pulses; then the hum settles and holds; "
               "no music.",
)


# ─────────────────────────── 提示词装配 ───────────────────────────

def h3_prompt(shot):
    """参考图生视频模式的提示词（保留 <Picture i> 引用）。"""
    s = SHOTS[shot]
    out = []
    out.append("subject_definitions:")
    out += s["subjects"]
    out.append("<Picture 1> is the first frame of [Shot 1]: " + s["first"])
    out.append("")
    out.append("summary:")
    out.append("[keyframe completion + reference generation] The target video starts from "
               "<Picture 1> as its exact first frame: " + s["summary"] +
               " <Picture 2> and <Picture 3> define <Subject 1>'s identity and clothing only.")
    out.append("")
    out.append("retention_analysis:")
    out += s["retention"]
    out.append("<Picture 1> ([Shot 1] first frame): fully_preserved - the video opens on this "
               "exact frame and develops forward from it.")
    out.append("")
    out.append("detailed_description:")
    out.append(CAM_HEAD + "; " + s["camera"] + ".")
    out.append("[Shot 1] The shot begins from <Picture 1>: the opening frame of <Picture 1> is "
               "held exactly, then the action develops forward from it. "
               + " ".join(s["beats"]) + " " + s["close"])
    out.append("")
    out.append("overall_soundscape: " + s["sound_text"])
    out.append("")
    out.append("non_diegetic_music: N/A")
    return "\n".join(out)


def i2v_prompt(shot):
    """图生视频模式的提示词：首帧由节点 first_frame 作**几何锚点**，
    因此不能再用 <Picture 1> 指代首帧（该模式没有 ref_image_1）。
    <Picture 2> / <Picture 3>（定妆卡 / 全身正面）仍作为身份参考保留。"""
    p = h3_prompt(shot)
    p = p.replace(" in <Picture 1>:", " (as established in the provided first frame):")
    p = p.replace("<Picture 1> is the first frame of [Shot 1]: ",
                  "The provided first frame of [Shot 1] shows: ")
    p = p.replace("The target video starts from <Picture 1> as its exact first frame:",
                  "The target video continues directly from the provided first frame:")
    p = p.replace("<Picture 1> ([Shot 1] first frame): fully_preserved - the video opens on this "
                  "exact frame and develops forward from it.",
                  "The provided first frame (the [Shot 1] keyframe): fully_preserved - the video "
                  "opens on this exact frame and develops forward from it.")
    p = p.replace("as in <Picture 1>.", "as in the provided first frame.")
    p = p.replace("in <Picture 1>", "in the provided first frame")
    p = p.replace("[Shot 1] The shot begins from <Picture 1>: the opening frame of <Picture 1> "
                  "is held exactly, then the action develops forward from it.",
                  "[Shot 1] The shot begins exactly on the provided first frame: that frame is "
                  "held as the video's first frame, then the action develops forward from it.")
    return p


def build(prompt, first_img, seed, prefix, frames):
    """⚠️ 用 Yuan_MiniMaxH3Video · mode=图生视频 —— 首帧作几何锚点（corr 0.999 实测锁定）。
    不要换回 MiniMaxH3ReferenceToVideo：那个节点没有 first_frame 通道，首帧锁不住。"""
    return {
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_video_vae_fp16.safetensors"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_audio_vae_fp32.safetensors"}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "minimax\\qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "151": {"class_type": "DiffusionModelLoaderKJ", "inputs": {"model_name": "minimax\\minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default", "compute_dtype": "default", "patch_cublaslinear": False, "sage_attention": "auto", "enable_fp16_accumulation": True}},
        "137": {"class_type": "LoadImage", "inputs": {"image": first_img}},
        "139": {"class_type": "LoadImage", "inputs": {"image": "h3_ly_card.png"}},
        "145": {"class_type": "LoadImage", "inputs": {"image": "h3_ly_front.png"}},
        "136": {"class_type": "Yuan_MiniMaxH3Video",
                "inputs": {"mode": "图生视频", "clip": ["128", 0], "vae": ["119", 0],
                           "audio_vae": ["120", 0],
                           "prompt": prompt, "width": 480, "height": 832, "length": frames,
                           "ref_image_size": "匹配",
                           "first_frame": ["137", 0],
                           "ref_image_2": ["139", 0], "ref_image_3": ["145", 0]}},
        "126": {"class_type": "BasicGuider", "inputs": {"model": ["151", 0], "conditioning": ["136", 0]}},
        "124": {"class_type": "BasicScheduler", "inputs": {"model": ["151", 0], "scheduler": "simple", "steps": 25, "denoise": 1.0}},
        "123": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "129": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "125": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["129", 0], "guider": ["126", 0], "sampler": ["123", 0], "sigmas": ["124", 0], "latent_image": ["136", 1]}},
        "154": {"class_type": "VAEDecode", "inputs": {"samples": ["125", 0], "vae": ["119", 0]}},
        "121": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["125", 0], "vae": ["120", 0]}},
        "130": {"class_type": "CreateVideo", "inputs": {"images": ["154", 0], "fps": 24.0, "audio": ["121", 0], "bit_depth": 8}},
        "92": {"class_type": "SaveVideo", "inputs": {"video": ["130", 0], "filename_prefix": prefix, "format": "auto", "codec": "auto"}},
    }


# ─────────────────────────── 执行 ───────────────────────────

def upload(path, name, tries=5):
    data = Path(path).read_bytes()
    for k in range(tries):
        try:
            r = S.post(HOST + "/upload/image", files={"image": (name, data, "image/png")},
                       data={"overwrite": "true"}, timeout=(10, 300))
            r.raise_for_status()
            return r.json()["name"]
        except Exception as e:
            print("     上传重试 %d/%d: %s" % (k + 1, tries, e), flush=True)
            time.sleep(5)
    raise RuntimeError("upload failed: " + str(path))


def fetch(url, out, tries=4):
    for k in range(tries):
        try:
            with S.get(url, timeout=(10, 900), stream=True) as r:
                r.raise_for_status()
                with open(out, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            return True
        except Exception as e:
            print("     下载失败(%d/%d): %s" % (k + 1, tries, e), flush=True)
            time.sleep(10)
    return False


PENDING = []   # 下载失败待取回清单


def gen(shot):
    s = SHOTS[shot]
    src = P.frame_path(FRAME_FILE[shot])
    if not src.exists():
        print("[%s] 首帧缺失 %s" % (shot, s["frame"])); return
    out = OUT_DIR / ("%s_%s.mp4" % (shot, s["name"]))
    if out.exists() and out.stat().st_size > 50_000:
        print("[%s] 已存在，跳过" % shot); return

    first = upload(src, "h3_%s_first.png" % shot)
    seed = 2026091200 + int(shot[1:])
    wf = build(i2v_prompt(shot), first, seed, "h3/ep01v3_%s" % shot, s["frames"])

    t0 = time.time()
    try:
        r = S.post(HOST + "/prompt", json={"prompt": wf}, timeout=(10, 120))
        r.raise_for_status()
        pid = r.json()["prompt_id"]
    except Exception as e:
        body = ""
        try:
            body = r.text[:500]
        except Exception:
            pass
        print("[%s] 提交失败: %s %s" % (shot, e, body), flush=True); return
    print("[%s] 提交 pid=%s frames=%d (%.1fs)" % (shot, pid, s["frames"], s["frames"] / 24.0), flush=True)

    while True:
        time.sleep(15)
        try:
            h = S.get(HOST + "/history/" + pid, timeout=20).json()
        except Exception:
            continue
        if pid not in h:
            continue
        st = h[pid].get("status", {}).get("status_str")
        if st == "error":
            for m in h[pid]["status"].get("messages", []):
                if m[0] == "execution_error":
                    print("[%s] 执行错误 node=%s: %s"
                          % (shot, m[1].get("node_type"), str(m[1].get("exception_message"))[:400]))
            return
        got = False
        for node, v in h[pid].get("outputs", {}).items():
            for key in ("videos", "gifs", "images"):
                for it in v.get(key, []) or []:
                    fn = it.get("filename")
                    if not fn:
                        continue
                    url = "%s/view?filename=%s&subfolder=%s&type=output" % (
                        HOST, requests.utils.quote(fn), requests.utils.quote(it.get("subfolder", "")))
                    OUT_DIR.mkdir(parents=True, exist_ok=True)
                    if fetch(url, out):
                        print("[%s] OK %.0fs -> %s (%.1f MB)"
                              % (shot, time.time() - t0, out.name, out.stat().st_size / 1e6), flush=True)
                        got = True
                    else:
                        PENDING.append({"shot": shot, "pid": pid, "filename": fn,
                                        "subfolder": it.get("subfolder", "")})
                        print("[%s] 已生成但下载失败，记入待取回（pid=%s）" % (shot, pid), flush=True)
                        got = True
        if not got:
            print("[%s] 完成但未取到产物: %s" % (shot, json.dumps(h[pid].get("outputs", {}), ensure_ascii=False)[:300]))
        return


if __name__ == "__main__":
    for k, v in SHOTS.items():
        v.setdefault("sound", "")
    args = sys.argv[1:] or ["s01"]
    targets = list(SHOTS.keys()) if args == ["all"] else args
    n1 = upload(CARD, "h3_ly_card.png")
    n2 = upload(FRONT, "h3_ly_front.png")
    print("角色参考已上传:", n1, n2, flush=True)
    bad = []
    for s in targets:
        if s not in SHOTS:
            print("未知镜号", s); continue
        try:
            gen(s)
        except Exception as e:
            print("[%s] 异常 %s: %s" % (s, type(e).__name__, e), flush=True)
            bad.append(s)
    if PENDING:
        p = OUT_DIR / "_待取回.json"
        p.write_text(json.dumps(PENDING, ensure_ascii=False, indent=2), encoding="utf-8")
        print("待取回清单 ->", p)
    print("done. 尝试 %d 镜 | 异常 %d 镜 %s" % (len(targets), len(bad), bad if bad else ""))

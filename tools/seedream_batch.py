# -*- coding: utf-8 -*-
"""ep01 分镜图 · Seedream 5.0 Pro 批量生成
用法:
  python seedream_batch.py s01 s02 s03 ...      # 指定镜号
  python seedream_batch.py all                  # 全部
输出: releases/2026-09-12_ep01_成片包/02_分镜首帧/<镜号>_<名>.png
"""
import base64
import json
import os
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths as P

API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
MODEL = "doubao-seedream-5-0-pro-260628"
ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
OUTDIR = P.EP01_FRAMES
LUYUAN = ROOT / "input" / "juese" / "luyuan" / "luyuan.png"
LUYUAN_FRONT = ROOT / "input" / "juese" / "luyuan" / "三视图" / "front.png"
SIZE = "1152x2048"          # 9:16 竖屏（Pro 允许 921,600–4,624,220 总像素）

env = Path.home() / ".workbuddy" / ".env"
KEY = None
for line in env.read_text(encoding="utf-8").splitlines():
    if line.startswith("ARK_API_KEY="):
        KEY = line.split("=", 1)[1].strip()
        break
if not KEY:
    sys.exit("ERROR: ARK_API_KEY not found")

# ── 全局风格基底（visual-spec-lock 暖调清洁配方 · 中英混写） ──
# ⚠️ 2026-09-12：移除全部否定词（not desaturated/not gray/not cold/no film grain）
#    原因：Seedream 无 negative prompt，否定词会反向强化被否定的概念（实测 s07 -9.3→+37.2）
W = ("写实电影质感，35mm 全画幅，暖调钨丝主光，琥珀色高光，干净的暖色阴影，"
     "自然肤色偏暖，锐利清晰，干净画面，浅景深，180 度快门，竖屏 9:16 构图。"
     "photorealistic, 35mm full-frame cinematic still, warm tungsten key light, "
     "amber highlights, clean warm shadows, natural skin with warm undertone, "
     "sharp focus, crisp detail, clean image, shallow depth of field, 180-degree shutter, "
     "vertical 9:16 composition, rich saturated warm colors, clean crisp rendering")
DUSK = "黄昏金色逆光，长长的影子，暖色空气。golden hour backlight, long shadow"
# 配给点·机构场景统一光色（s07–s11 同源；作者 2026-09-12 定："都使用 7"）
INST_WARM = ("配给点内部是明亮整洁的空间：浅米色墙面、直线条、没有装饰；头顶的暖色照明把整个空间照得明亮，"
             "所有人物和墙面都浸在温暖的琥珀色调里，皮肤是健康的暖色，整个画面温暖明亮、像午后室内。"
             "warm beige institutional interior, warm ambient overhead light, amber overall tone, "
             "clean bright space, warm healthy skin tones, bright and warm")
# 配给点轴线（s07–s11 五镜共用 · 作者 2026-09-12 指出"7是对着屏幕，后面的都是对着观众"）
# 铁律：他在窗口前面对的是屏幕，观众只能看到他的侧后 3/4 —— 五镜朝向必须一致，不许正面对镜头
AXIS_WINDOW = ("**四分之三侧后角度**：他侧身站在配给点窗口前，面向画面右侧的一块淡色屏幕，screen 在画面右侧，"
               "**他不看镜头**；屏幕的光从侧面照在他的侧脸和眼镜边缘。"
               "three-quarter back view, he stands at an institutional counter facing the pale screen on the right, "
               "he never faces the lens, screen light hitting his face from the side")

# ── 锚点图（P0 一致性：场景/道具必须作为 image 参考传入，不能只写文字）──
ADIR = P.EP01_FRAMES
A1 = ADIR / "A1_废品收购站场景.png"
A2 = ADIR / "A2_锈迹斑斑的旧设备.png"
A3 = ADIR / "A3_充电头怼三孔圆口.png"
A4 = ADIR / "A4_手机屏幕2%.png"

# 多图参考时，自动为每张非角色锚点生成"保持什么不变"的说明（编号 = image N）
REF_NOTE = {
    "A1_废品收购站场景.png": "保持 image {i} 里的废品收购站场景结构、堆料布局、塑料棚形态与光线方向不变，只改变机位与人物动作。",
    "A2_锈迹斑斑的旧设备.png": "保持 image {i} 里那台旧机器的外观、锈蚀质感、面板与侧面形态完全一致。",
    "A3_充电头怼三孔圆口.png": "保持 image {i} 里充电头与插孔的形制、材质、磨损程度与年代感一致。",
    "A4_手机屏幕2%.png": "保持 image {i} 里那块手机的机身形制与旧界面风格一致。",
}

# ── 夜戏统一光色（s22–s25 四镜共用；作者定"统一修改"）──
# 要点：正向描述"巷子被照亮"，不写任何"暗/black"字样
NIGHT_WARM = ("夜里，老城区巷子被暖橙色的路灯整条照亮，光线是舒服的琥珀色；"
              "路灯光是画面里的主光源，把人物、墙面和堆着的废品都照得清楚，暗部仍是暖褐色、层次分明；"
              "主体明亮、五官和细节都清晰可见。"
              "well-lit night alley, warm amber street lamp as the main light source illuminating the whole lane, "
              "clearly visible subject, crisp facial features, warm brown tones in the shadow areas, bright and readable")



INST = "浅灰色机构内部空间，冷白荧光补光，但皮肤保持暖色。cool fluorescent fill but keep skin warm"

LY_REF = "用 image 1 中的人物（陆远）：30 岁出头的清瘦中国男人，身高 175cm 偏瘦精干，黑色短发微乱，戴旧黑框眼镜（左镜片有划痕、镜腿缠着胶带），洗白的格子衬衫（领口磨损），深色工装裤，指甲缝有油灰。保持他的脸、体型、眼镜、服装完全一致"

SHOTS = {
    # ── 锚点 A3 + s01：全集第一帧钩子（特写，无角色正脸） ──
    "s01": ("A3_充电头怼三孔圆口", None, (
        "极端特写：一只男人的手捏着一个 2026 年款的两脚扁插充电头，正怼向墙上一个三孔的圆口插座——插不进去，两个扁脚悬在圆孔外面。"
        "指腹碾过那两片被磨得发亮的铜脚。背景是一间破败废弃屋的墙，墙皮斑驳，清晨微弱的光从钉着塑料布的窗户透进来，"
        "灰尘在光柱里浮动。" + W)),

    # ── 锚点 A1：废品收购站的场景建立（无角色） ──
    "s13": ("A1_废品收购站场景", None, (
        "一条老城区巷子的拐角，堆着小山一样的废旧物品：生锈的机器外壳、铁皮、拆了一半的旧冰箱、"
        "一摞看不出牌子的旧显示器、缠绕的电线、几只铁桶。头顶上方搭着一块破损的塑料棚布，"
        "午后强烈的阳光从塑料棚的破洞里斜射下来，光柱里浮着灰尘。地面是水泥，有油渍。"
        "没有人物。竖构图，空间向画面深处堆叠。warm afternoon sunlight, hard key from side, dust in light beam。" + W)),

    # ── 锚点 A2：那台旧设备（道具 · 含侧面电源口） ──
    "s15": ("A2_锈迹斑斑的旧设备", None, (
        "中景：一台半人高的旧机器立在废品堆旁边，锈得看不出本来颜色，锈皮一块块翘起剥落，"
        "侧面有一块被拨开锈皮露出的控制面板，面板上有一个积着灰的拨杆。"
        "机身侧面下方有一个积满灰的两脚扁插电源口。机器屏幕上还亮着一片老旧的界面微光。"
        "午后侧光，浅景深。" + W)),

    # ── 锚点 A4：2026 手机屏幕（2%）★集尾 ──
    "s24": ("A4_手机屏幕2%", LUYUAN, (
        LY_REF + "。极端特写：一只沾着油灰的手里握着一部老旧的手机，手机屏幕刚刚亮起，"
        "屏幕上是 2026 年风格的旧界面（旧字体、旧图标），右上角显示「2%」的电量。"
        "手机屏幕是画面里最亮的光源，把他的半张脸、镜片反光和颧骨照得清清楚楚，皮肤纹理和眼镜细节都清晰可见。"
        "背景是夜里的暖橙色，路灯光从后面晕开。" + NIGHT_WARM + "画面安静、克制，他很明亮，一眼就能看清。竖构图。"
        "well-exposed close-up, brightest light source is the phone screen, face fully lit and clearly readable, "
        "crisp details, high clarity, bright and readable" + W)),

    # ── s17：陆远蹲在旧设备前（屏幕光映脸 · 正脸镜） ──
    "s17": ("s17_屏幕光映脸", [LUYUAN, A1, A2], (
        LY_REF + "。把他放进一间堆满废品的巷子角落，傍晚黄昏侧光。他蹲在一台锈迹斑斑的旧机器前，"
        "机器的屏幕亮着一片旧时代的界面，冷白色的屏幕光映在他的眼镜和颧骨上，他的表情空白而静止，"
        "没有惊讶也没有感动。空气里有浮尘。中近景，竖屏构图。" + W)),

    # ── s14：无所事事缓冲段（全集最重要一镜） ──
    "s14": ("s14_无所事事坐着", [LUYUAN, A1], (
        LY_REF + "。中景：他坐在废品堆旁边的地上，背靠着墙根，一条腿屈起，两只手搭在膝盖上，"
        "什么都没干，就是坐着——不是颓废，是那种「没地方去」的闲坐。"
        "头顶上方的塑料棚布破了一个洞，一束午后的阳光斜落下来照在他的鞋上。"
        "空气里有一只苍蝇。他微微低着头，视线落在前方的地上。远处是堆成小山的废旧物品。"
        "画面安静、日常、有暖意。中全景，竖屏构图。" + W)),

    # ══ 以下为剩余 19 镜 ══
    # 场1 晨·废弃屋
    "s02": ("s02_蹲地碾铜脚", LUYUAN, (
        LY_REF + "。中景：他蹲在一间破败废弃屋的墙角插座下面，一只手捏着那个充电头，拇指碾过铜脚，"
        "低头看着手里的东西。屋里没有床，是一摞纸箱板垫的；窗户没玻璃，钉着半透明塑料布，风一吹鼓起来。"
        "纸箱板上印着 2020 年代的印刷体，边缘有一行手写的批注。清晨微弱的天光从塑料布透进来。"
        "画面安静、清贫、不煽情，竖屏构图。" + W)),

    # 场2 街头
    "s03": ("s03_被当成噪音", LUYUAN, (
        LY_REF + "。中全景（竖构图，人小环境大）：他站在老城区一条旧街的中间偏下位置，微微抬着下巴，"
        "像在找一个愿意看他一眼的人。周围几个街坊从他两侧匆匆走过——前景一个走过的人影带着轻微运动模糊切过画面，"
        "挡住半边视线；没有一个人看他。不是被围观，是被当成噪音。他手里攥着一块手机大小的东西。"
        "上午硬光从侧面来，他脸上一半亮一半暗，地面有长长的影子。画面有流动感和被穿过感。" + W)),

    "s04": ("s04_让你的模型来问", LUYUAN, (
        LY_REF + "（画面右侧是他的背影，只露肩膀和侧脸，略虚）。画面主体是一个拎着菜的中年女人："
        "五十岁上下，短发，深色外套，臂弯里挎着装菜的布袋。她戴着一副极小的无线耳机——"
        "肤色入耳式，几乎看不见，耳朵周围没有任何线。她低着头对着空气说话（不是对镜头、也不是对陆远），"
        "视线落在空气里，态度平淡。老城区街头，上午阳光，暖调。两人中景，一前一后，竖构图。"
        "no wires, no cables, no headphones band, invisible in-ear device, seamless future tech" + W)),

    "s05": ("s05_你没登记吧", LUYUAN, (
        LY_REF + "站在画面左侧（正面偏侧，手里攥着那块手机大小的东西）。画面主体是一个卖旧零件的中年摊主："
        "五十岁上下，旧夹克，正低头用一块脏布擦一堆螺丝，抬眼看过来的一瞬间——不是恶意，是见多了的那种平淡。"
        "摊子上摆着旧螺丝、旧零件、几只铁盒。"
        "**午后强烈的暖色侧光**从侧面照下来，阳光打在他的手背、摊主的肩膀和金属零件上，金属反出暖色，"
        "两个人的皮肤都保持暖色，画面整体温暖明亮、绝不偏冷不偏灰。两人中景，竖构图。"
        "warm afternoon sunlight, hard warm key from side, warm skin tones, warm overall cast" + W)),

    # 场3 配给点
    "s06": ("s06_配给点长队", LUYUAN, (
        LY_REF + "（他站在队伍末端，位于画面下方，略虚）。竖构图，一个配给点的队伍："
        "一排人贴着浅灰色的机构墙面排成一列安静的长队，向画面深处延伸。队伍里所有人都低着头，"
        "各自对着空气低声说话，彼此之间没有交谈、没有插队、没有催促——整条队伍安静得像一排待办事项。"
        "画面中部，一个穿深色外套的男人正抬手看自己的手腕，腕上一个黑色设备闪了一下，"
        "前方的闸机亮起放行，他脚步没停就走了进去；周围排队的人没有任何反应，像这本来就正常。"
        "画面下方：陆远站在队伍里，也低头看了一眼自己的手腕——手腕上是空的。"
        "浅灰机构内部墙面，冷白荧光补光，人物皮肤保留暖色。没有人正脸看镜头。纪实感，竖屏。" + W + " " + INST)),

    "s07": ("s07_核验失败", LUYUAN, (
        LY_REF + "。中近景。" + AXIS_WINDOW + "他刚站定，肩膀稍微绷着，没有愤怒，只是站着。"
        + INST_WARM + "竖构图。" + W)),

    "s08": ("s08_预约死循环", LUYUAN, (
        LY_REF + "。中近景，同一机位。" + AXIS_WINDOW + "他的表情是空的、耐心的——像一个人已经知道答案但还是站着。"
        + INST_WARM + "浅景深，竖构图。" + W)),

    "s09": ("s09_方案与选择", LUYUAN, (
        LY_REF + "。中近景，同一机位。" + AXIS_WINDOW + "他的眼睛微微睁大了一点点——"
        "不是震惊，是「听懂了」的那一下。嘴唇没有张开。" + INST_WARM + "浅景深，竖构图。" + W)),

    "s10": ("s10_哪部分经历", [LUYUAN, A4], (
        LY_REF + "。面部特写，**四分之三侧脸**：他微微低头，视线垂下来落在自己手里那部黑色的手机上。"
        "屏幕的光照在他的下半张脸和眼镜下缘，眼睛在镜片后面的暗处。表情极安静。**他不看镜头**。"
        + INST_WARM + "浅景深，竖构图。"
        "three-quarter side view of the face, looking down at the phone in his hand, never facing the lens" + W)),

    "s11": ("s11_把家卖了", LUYUAN, (
        LY_REF + "。中近景，同一机位。" + AXIS_WINDOW + "他侧身站在窗口前低声说话；"
        "身后的人群正在往前涌、把他往边上挤，前景几个模糊的肩膀和手臂切过画面，他的身体略微倾斜但仍然站着。"
        + INST_WARM + "轻微动态模糊，竖构图。" + W)),

    "s12": ("s12_街边逆光", [LUYUAN, A3], (
        LY_REF + "。中景：他站在配给点外面的街边，中午强烈的太阳从他背后斜射过来，把他的轮廓压成一道剪影，"
        "脸在暗部但有暖色反光。他低着头看手里攥着的那块黑色的东西（一块 2026 年的手机）。"
        "街边水泥地反光很亮。写实，竖构图，不悲情。" + W)),

    # 场4 废品收购站
    "s16": ("s16_拨了一下", [A2], (
        "中近景：一只男人的手（指甲缝有油灰）刚把一个旧面板上的拨杆从一侧拨到另一侧，"
        "那台半人高的锈迹斑斑的旧机器屏幕刚刚亮起一片老旧的界面——旧字体、旧图标，微弱的光。"
        "能看清机器侧面的锈皮、面板上的灰、和手背上的细小划痕。午后侧光，浅景深，竖构图。" + W)),

    "s18": ("s18_怎么修好的", [LUYUAN, A1, A2], (
        LY_REF + "。黄昏金色逆光。他蹲在那台锈迹斑斑的旧机器前（画面左侧），"
        "两步外站着一个瘦削的老人：七十岁上下，灰扑扑的旧外套，拎着一个编织袋，微微弓背，没有走近。"
        "两个人之间的距离感很清楚——不是亲近，是陌生人之间留出的那两步。空气里有暖色浮尘，长长的影子。"
        "中景两人，竖构图。" + W + " " + DUSK)),

    "s19": ("s19_塞干粮与硬币", None, (
        "极端特写：一只苍老粗糙的手（青筋、老茧、指甲发黑）正把一个小布包里的东西按进另一只年轻的手掌里——"
        "半袋干粮（压缩饼干一样的东西）和两枚旧硬币。两只手都沾着灰。"
        "黄昏金色暖光，浅景深，背景虚化成一片暖色。竖构图。" + W + " " + DUSK)),

    "s20": ("s20_别往新城区说", [A1], (
        "黄昏。中近景：一个瘦削的老人（七十岁上下，灰扑扑旧外套，拎着编织袋）侧背着镜头，"
        "脸只露出一个侧影，正压低声音说话，视线往画面外看（像是在看四周有没有人）。"
        "背景是堆着废品的巷子口，金色逆光，长长的影子。他的姿态是谨慎的、要走的。竖构图。" + W + " " + DUSK)),

    # 场5 暮·巷口
    "s21": ("s21_三种人吃东西", [LUYUAN, A1], (
        LY_REF + "蹲在画面左侧，手里拿着干粮在吃（侧脸）。画面右侧蹲着一个二十来岁的年轻人："
        "短袖，瘦，腰上挂着一个巴掌大的白色盒子，一根细管贴在小腹位置，正盯着陆远手里的干粮看。"
        "暮色巷口，暖橙色的路灯刚亮起，两个人蹲在地上，中间隔着一点距离。"
        "市井、日常、不煽情。中景两人，竖构图。" + W)),

    # 场6 夜
    "s22": ("s22_摸到兜里那个", [LUYUAN, A1, A2], (
        LY_REF + "。中景：他走在老城区的巷子里（背景结构与堆料同 image 2），"
        "刚走了两步又停住，一只手插在裤兜里，身体微微侧过来。" + NIGHT_WARM +
        "路灯光在他脸侧勾出一道暖色轮廓光。竖构图。" + W)),

    "s23": ("s23_插上电源口", [LUYUAN, A2], (
        LY_REF + "。中近景：他蹲在那台旧机器旁边（机器的外观、锈蚀与形态同 image 2），侧身对着镜头，微微低着头。"
        "他的一只手伸向机器侧面下方——那只手只看出一个轮廓，动作本身不在焦点上。"
        "画面焦点在他的脸：下方微弱的暖光刚刚亮起来，映亮他的下半张脸、眼镜下缘和下颌，"
        "他的神情安静、专注，像在做一件很平常的事。" + NIGHT_WARM + "竖构图。"
        "no visible socket, no visible plug, no mechanical detail, mechanism out of frame, "
        "focus on his face and the soft glow rising from below" + W)),

    "s25": ("s25_他抬起头", [LUYUAN, A1, A2], (
        LY_REF + "。中近景：他蹲在那台旧机器前（机器同 image 3、场景同 image 2），机器屏幕刚刚又亮了一下，"
        "他正抬起头看向机器屏幕（视线向上，侧脸对着镜头），机器屏幕的光和路灯的光一起照在他脸上，"
        "他的侧脸轮廓和眼镜清清楚楚。他脸上没有表情，只是看着。" + NIGHT_WARM + "竖构图。" + W)),
}


def data_uri(p):
    p = Path(p)
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(p.suffix.lower().lstrip("."), "png")
    return "data:image/%s;base64,%s" % (mime, base64.b64encode(p.read_bytes()).decode())


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(26)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def gen(shot):
    if shot not in SHOTS:
        print("skip unknown", shot); return
    name, ref, prompt = SHOTS[shot]
    refs = []
    if ref:
        refs = list(ref) if isinstance(ref, (list, tuple)) else [ref]
    refs = [Path(r) for r in refs if Path(r).exists()]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    dst = OUTDIR / ("%s.png" % name)
    if dst.exists() and dst.stat().st_size > 100_000:
        print("[%s] exists, skip -> %s" % (shot, dst.name)); return
    # 自动为锚点参考生成"保持什么不变"的说明（image N 编号与 image 数组一致）
    notes = []
    for idx, r in enumerate(refs, start=1):
        note = REF_NOTE.get(r.name)
        if note:
            notes.append(note.format(i=idx))
    full = "".join(notes) + prompt
    payload = {
        "model": MODEL, "prompt": full, "response_format": "url",
        "size": SIZE, "output_format": "png", "watermark": False,
    }
    if refs:
        uris = [data_uri(r) for r in refs]
        payload["image"] = uris[0] if len(uris) == 1 else uris
        print("[%s] refs=%s" % (shot, ",".join(r.name for r in refs)))
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY}, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            res = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("[%s] HTTP %s: %s" % (shot, e.code, e.read().decode("utf-8", errors="replace")[:800]))
        return
    d = (res.get("data") or [{}])[0]
    url = d.get("url")
    if not url:
        print("[%s] no url: %s" % (shot, json.dumps(res, ensure_ascii=False)[:500])); return
    with urllib.request.urlopen(url, timeout=300) as r, open(dst, "wb") as f:
        f.write(r.read())
    sz = png_size(dst)
    print("[%s] OK %.0fs %s size=%s %s" % (shot, time.time() - t0, dst.name, sz, d.get("size", "")))


if __name__ == "__main__":
    args = sys.argv[1:] or ["s01"]
    targets = list(SHOTS.keys()) if args == ["all"] else args
    for s in targets:
        gen(s)
    print("done.")

# -*- coding: utf-8 -*-
"""ep01 短剧视频 · MiniMax H3 多参图生视频（25 镜）
链路：Seedream 首帧 → H3 参考生视频（带音频）
用法：
  python gen_ep01_h3.py s01            # 单镜（测速/调试）
  python gen_ep01_h3.py s01 s02 s03    # 指定多镜
  python gen_ep01_h3.py all            # 全部 25 镜
输出：releases/2026-09-12_ep01视频/<镜号>_<名>.mp4
"""
import json, os, sys, time, uuid, mimetypes, urllib.request, urllib.error
from pathlib import Path

HOST = "http://127.0.0.1:8188"
ROOT = Path(r"C:\Users\oo\WorkBuddy\小说未来ai")
FRAME_DIR = ROOT / "releases" / "2026-09-12_ep01分镜图"
OUT_DIR = ROOT / "releases" / "2026-09-12_ep01视频"
CARD = ROOT / "input" / "juese" / "luyuan" / "luyuan.png"          # <Picture 2>
FRONT = ROOT / "input" / "juese" / "luyuan" / "三视图" / "front.png"  # <Picture 3>

V = "The target video is a photorealistic documentary-style vertical 9:16 shot"

# 镜号 → (首帧文件名, 中文名, 帧数 length=124+17k)
SHOTS = {
    "s01": ("A3_充电头怼三孔圆口.png", "插不进插座",   141),
    "s02": ("s02_蹲地碾铜脚.png",     "碾铜脚",       175),
    "s03": ("s03_被当成噪音.png",     "被当成噪音",    175),
    "s04": ("s04_让你的模型来问.png", "让你的模型来问", 209),
    "s05": ("s05_你没登记吧.png",     "你没登记吧",    260),
    "s06": ("s06_配给点长队.png",     "配给点长队",    175),
    "s07": ("s07_核验失败.png",       "核验失败",     209),
    "s08": ("s08_预约死循环.png",     "预约死循环",    260),
    "s09": ("s09_方案与选择.png",     "方案A与B",     260),
    "s10": ("s10_哪部分经历.png",     "哪部分经历",    209),
    "s11": ("s11_把家卖了.png",       "把家卖了",     311),
    "s12": ("s12_街边逆光.png",       "街边逆光",     175),
    "s13": ("A1_废品收购站场景.png",  "废品收购站",    141),
    "s14": ("s14_无所事事坐着.png",   "无所事事",     260),
    "s15": ("A2_锈迹斑斑的旧设备.png", "旧设备",       209),
    "s16": ("s16_拨了一下.png",       "拨了一下",     192),
    "s17": ("s17_屏幕光映脸.png",     "屏幕光映脸",    209),
    "s18": ("s18_怎么修好的.png",     "怎么修好的",    294),
    "s19": ("s19_塞干粮与硬币.png",   "塞干粮硬币",    294),
    "s20": ("s20_别往新城区说.png",   "别往新城区说",   294),
    "s21": ("s21_三种人吃东西.png",   "三种人",       294),
    "s22": ("s22_摸到兜里那个.png",   "摸到兜里那个",   209),
    "s23": ("s23_插上电源口.png",     "插上电源",     209),
    "s24": ("A4_手机屏幕2%.png",      "手机2%",      192),
    "s25": ("s25_他抬起头.png",       "他抬起头",     175),
}

# 每镜：(场景 desc, 首帧 desc, 一句话 summary, 主体保留度, 光, 分时动作, 环境音)
P = {}

P["s01"] = (
    "the worn interior wall and the round three-hole white socket in <Picture 1>, with a plastic-sheeted window leaking warm dawn light and floating dust",
    "an extreme close-up of a rough hand pressing a worn grey two-pin charger toward the round socket, the flat pins misaligned with the round holes",
    "the hand tries to force the old two-pin charger into the round socket, fails twice, and finally hangs in mid-air between retries",
    "partially_preserved — only his hand and plaid shirt cuff appear; his face never enters the frame",
    "warm morning light through plastic sheeting",
    "From 00:00.5, the hand pushes the charger against the socket; the flat prongs catch the ceramic rim, scrape, and slip aside. From 00:01.8, the wrist rotates to try another angle; the prongs slip off again and the thumb rubs over the polished copper prongs. From 00:03.4, the hand pulls the charger a few centimetres away and holds it in mid-air; the handheld camera dips slightly and settles on the gap between plug and socket",
    "quiet room tone, faint electrical hum, wind pressing the plastic sheet, a dry ceramic scraping sound on each slip, distant traffic",
)

P["s02"] = (
    "the bare room in <Picture 1>: a bed of stacked flattened cardboard boxes, a plastic sheet taped over the window, warm morning light cutting in with floating dust",
    "a medium shot of him crouched under the wall socket, holding the charger in one hand with his thumb on the copper contacts, head lowered",
    "he stays crouched, slowly rubs the worn copper prongs with his thumb, glances at the room, then tucks the charger into his pocket and stands up",
    "fully_preserved — face, glasses, plaid shirt and crouched posture all retained",
    "warm morning light through the plastic sheet",
    "From 00:00.0, his thumb rubs slowly back and forth over the polished copper prongs, small and repetitive, as if confirming by touch. From 00:02.6, he lifts his head and looks across the room: the stacked cardboard, the plastic-sheet window bulging inward with a gust. From 00:05.0, he lowers his gaze, closes his fingers around the charger and slips it into his pocket, then rises to his feet; the handheld camera drifts up with him",
    "quiet room tone, wind pressing the plastic sheet, a distant street ambience beginning",
)

P["s03"] = (
    "an old-town street in the daytime, pedestrians passing",
    "him standing still in the middle of the old-town street, pedestrians crossing on both sides, nobody looking at him",
    "he stands still in the middle of the street while pedestrians walk past on both sides without a glance",
    "fully_preserved — face, glasses, plaid shirt retained",
    "hard late-morning sunlight from the side",
    "From 00:00.0, he stands still with his chin slightly raised; pedestrians pass on both sides, and one figure crosses the close foreground with light motion blur, blocking half the frame for a beat. From 00:03.0, he turns his head slowly to follow a passer-by, but nobody meets his eyes. From 00:05.5, he lowers his chin and closes his fingers around the small object in his hand; the handheld camera drifts slightly and lets the passers-by keep crossing",
    "busy old-town street ambience, footsteps, distant market noise",
)

P["s04"] = (
    "an old-town street in the morning, with a middle-aged woman carrying a cloth bag of vegetables (a separate character, not <Subject 1>), her ears carrying no wires at all",
    "a middle-aged woman speaking to the air with her head down, wearing an invisible in-ear device, while his back and shoulder fill the right edge of the frame in soft focus",
    "the woman answers him without looking up, telling him to let his model do the asking",
    "partially_preserved — only his back and shoulder are in frame; the woman is a separate character",
    "warm late-morning sunlight",
    "From 00:00.5, the woman speaks to the air with her head down, lips moving, no earphone wire anywhere. From 00:03.0, she glances up at him for a single beat — she notices his glasses — then looks away and walks off past the camera. From 00:05.6, his back shifts slightly at the right edge of frame but he does not follow her; the camera holds on the space she left",
    "street ambience, her voice carrying on the air, footsteps receding",
)

P["s05"] = (
    "a small street stall selling old screws and parts, run by a middle-aged man in an old jacket who wipes a pile of screws with a rag (a separate character)",
    "him standing at the left of frame holding the small black device, facing a middle-aged man at his stall who is looking up from wiping screws",
    "the man at the stall looks up and tells him he is not registered, then sends him to the ration point",
    "fully_preserved — face, glasses, plaid shirt retained",
    "warm hard afternoon sunlight from the side, metal parts catching the light",
    "From 00:00.3 to 00:02.5, two brief impressions pass (a hand waving him off, a lowered head). From 00:03.0, the middle-aged man looks up from his rag and speaks while still wiping; sunlight catches the metal parts on the stall. From 00:06.2, he answers and the man gestures down the street with his chin. From 00:08.0, the man returns to wiping; he stands a beat longer, then turns away",
    "street ambience, cloth rubbing metal, coins shifting in a tin",
)

P["s06"] = (
    "the institutional ration-point counter in <Picture 1>, with a quiet queue of people standing along the pale wall (separate characters, not <Subject 1>)",
    "a quiet queue standing along a pale institutional wall, while he stands at the near end of the queue looking down at his own empty wrist",
    "the queue stands silent; one man raises his wrist, a gate reads it and opens, he walks through without stopping, and nobody reacts",
    "fully_preserved — face, glasses, plaid shirt retained at the near end of the queue",
    "warm institutional overhead light",
    "From 00:00.0, the queue stands motionless along the wall, everyone looking down and murmuring at the air. From 00:02.0, a man in a dark jacket lifts his wrist; a black device glints and a gate ahead lights up and opens; he walks through without breaking stride while the people around show no reaction at all. From 00:04.5, he looks down at his own bare wrist and holds it there; the camera holds on him at the near end of the queue",
    "institutional room tone, a soft gate chime, low murmuring along the queue",
)

P["s07"] = (
    "the institutional counter in <Picture 1> with a pale screen on the right",
    "him standing side-on at the counter in three-quarter back view, facing the pale screen on the right, screen light on his profile and the edge of his glasses",
    "a synthetic voice reports that he is not in the system, and he answers that he is here to register",
    "fully_preserved — three-quarter back view, face and glasses partly visible",
    "warm institutional overhead light",
    "From 00:00.3, a clean synthetic female voice comes from the screen off-frame right; he stays in three-quarter back view and does not turn toward the lens. From 00:04.2, he answers quietly and his head turns a few degrees toward the screen. From 00:06.8, the screen keeps scrolling with no answer; his shoulders stay level and the camera holds absolutely still",
    "institutional room tone, a clean synthetic female voice, faint ventilation hum",
)

P["s08"] = (
    "the institutional counter in <Picture 1> with the pale screen on the right",
    "him standing side-on at the counter in three-quarter back view, facing the pale screen, screen light on his cheek",
    "the loop plays out: registration needs a booking, a booking needs an identity, and he answers each one flatly",
    "fully_preserved — three-quarter back view",
    "warm institutional overhead light",
    "From 00:00.3, the synthetic voice states each requirement in turn; he answers each one without moving his feet, always in three-quarter back view, never facing the lens. By 00:06.6 both have stopped; there is a long silence and the queue behind him begins to shift. The camera is locked off, only the screen light moving on his face",
    "institutional room tone, synthetic voice, the queue shuffling behind him",
)

P["s09"] = (
    "the institutional counter in <Picture 1> with the pale screen on the right",
    "him standing side-on at the counter in three-quarter back view, more of his face visible in profile, screen light on his eyes",
    "the voice offers plan A and plan B; plan B is to license his experience as training data, and his eyes widen by a fraction",
    "fully_preserved — three-quarter back view",
    "warm institutional overhead light",
    "From 00:00.3, the synthetic voice lays out plan A and plan B in a level tone and the screen keeps scrolling. From 00:07.2, he asks quietly what plan B is. From 00:09.0, the voice answers and his eyes widen by a fraction — no shock, only comprehension; his mouth stays closed. He never faces the lens",
    "institutional room tone, synthetic voice, quiet queue behind",
)

P["s10"] = (
    "the institutional counter in <Picture 1>",
    "a close-up of his three-quarter profile looking down at the black phone in his hand, screen light on his lower face",
    "he asks which part of his experience, and the voice answers: all of it",
    "partially_preserved — close-up on his face and hand",
    "warm institutional overhead light mixed with weak light from the phone",
    "From 00:00.5, he asks his question in a flat tone, eyes down on the phone. From 00:02.2, the voice answers off-frame. From 00:03.8, he asks about the things he remembers and the voice answers that memory is how experience is stored. From 00:05.6, he holds still, looking down; the camera holds on his three-quarter profile with dust drifting in the air",
    "institutional room tone, synthetic voice, a very faint phone buzz",
)

P["s11"] = (
    "the institutional counter in <Picture 1>, with the crowd behind him",
    "him standing side-on at the counter in three-quarter back view, the crowd pressing up behind him",
    "he says quietly that they are asking him to sell his home; the voice answers that the system does not judge plans, only provides them; then the crowd pushes him aside",
    "fully_preserved — three-quarter back view",
    "warm institutional overhead light",
    "From 00:00.5, he says the line quietly in three-quarter back view. From 00:03.7, the synthetic voice answers flatly. From 00:06.3, the people behind surge forward; blurred shoulders and arms cut across the foreground and push him out to the side of frame; he stumbles half a step but stays upright. The camera shakes slightly with the crowd",
    "institutional room tone, synthetic voice, a crowd surge, shuffling footsteps",
)

P["s12"] = (
    "the street outside the ration point at midday",
    "him standing at the kerb backlit, looking down at the small black device in his hand",
    "he stands in the hard midday sun holding the charger, then walks away",
    "fully_preserved — backlit silhouette, face in shadow with warm reflection",
    "hard midday sun from behind, rim light on his outline, bright pavement",
    "From 00:00.0, he stands still at the kerb, backlit, his outline dark against the bright pavement, looking down at the device in his hand. From 00:03.5, his thumb moves once over the copper prongs. From 00:05.0, he pockets the device and walks off down the street away from camera; the handheld camera lets him go and holds on the empty kerb",
    "midday street ambience, traffic, footsteps on concrete",
)

P["s13"] = (
    "the scrap-collection corner in <Picture 1> — no people in this shot",
    "the empty scrap corner: machine shells, sheet metal, a half-dismantled fridge, stacked monitors, a torn plastic canopy with a shaft of sunlight coming through",
    "an empty establishing shot: sunlight shifts, dust drifts, the scrap pile rests",
    "not present in this shot — no people appear",
    "warm afternoon sun through a hole in the canopy, dust in the beam",
    "From 00:00.0 to 00:04.0, the empty scrap corner holds still: dust drifts through the shaft of sunlight, the torn plastic canopy shifts a few centimetres in the wind, one loose sheet of metal rocks slightly. From 00:04.0 to 00:05.9, the patch of sunlight moves across the ground as the canopy settles; the camera creeps forward slowly toward the rusted machine at the right",
    "scrap-yard ambience, wind in the plastic canopy, a distant bicycle bell, sheet metal ticking",
)

P["s15"] = (
    "the rusted machine in <Picture 1> — a prop shot, no people",
    "the machine's flaking rust, a dusty control panel with a single lever, its screen showing a dim year-2026 interface",
    "the machine's screen stays lit; rust flakes fall, dust drifts, the old interface shifts by a line",
    "not present in this shot — no people appear",
    "warm afternoon side light",
    "From 00:00.0, the machine sits where it was left, its screen lit with the old interface; a few rust flakes fall from the panel edge. From 00:03.0, the interface on the screen advances by a line as the machine runs and a small indicator pulses. From 00:05.5, dust drifts past the screen in the side light; the camera creeps closer on the lever and panel. Nothing else moves",
    "a low electrical hum from the machine, scrap-yard ambience, wind",
)

P["s16"] = (
    "the machine's control panel in <Picture 1>",
    "a man's hand with oil-stained fingernails resting on the lever it has just flicked, the machine's screen just lighting up",
    "the hand flicked the lever once, and the machine's screen lights up",
    "partially_preserved — only the hand and forearm appear",
    "warm afternoon side light",
    "From 00:00.0, the hand stays on the lever where it flicked it; the machine's screen flickers and then holds a steady old interface. From 00:02.0, the hand withdraws a few centimetres, fingers half-curled, and stops. From 00:04.5, dust drifts through the side light across the panel; the hand stays absolutely still and the screen keeps glowing",
    "one soft click of the lever, then a rising electrical hum as the machine wakes, scrap-yard ambience",
)

P["s18"] = (
    "the scrap corner at golden hour, with a thin old man in a worn jacket holding a woven bag standing two steps away (a separate character, not <Subject 1>)",
    "him crouched by the machine on the left and the old man standing two steps off on the right, neither of them moving",
    "the old man asks how he fixed it; he answers that it was never broken, just a switch",
    "fully_preserved — face, glasses, plaid shirt retained",
    "golden hour backlight, long shadows, warm haze",
    "From 00:00.5, the old man speaks from two steps away without coming closer; he answers without turning his head, still crouched. From 00:04.0, he closes the panel and stands up, one hand on the machine because his leg has gone numb. From 00:07.0, the old man looks at the machine, then back at him, and says nothing more; both stay in the golden backlight",
    "golden hour scrap-yard ambience, the machine's hum, a distant dog, wind",
)

P["s19"] = (
    "golden hour, hands only in <Picture 1>",
    "an old weathered hand pressing a small cloth bundle of dry rations and two worn coins into a younger man's open palm",
    "the old man presses dry rations and two coins into his hand",
    "not present — only hands appear in this shot",
    "golden hour warm light",
    "From 00:00.0, the old hand presses the cloth bundle and two coins into the open palm, and the fingers close over them. From 00:02.5, the old hand withdraws and the young hand curls around the bundle, the thumb rubbing one coin once. From 00:04.5, both hands stay still in the warm light with dust drifting; the camera holds tight on the two hands",
    "cloth rustling, coins clicking together once, golden-hour street ambience",
)

P["s20"] = (
    "the scrap corner at golden hour, the old man in three-quarter back view (a separate character, not <Subject 1>)",
    "the thin old man in three-quarter back view, his profile just visible, speaking in a low voice, looking off to the side",
    "the old man warns him in a low voice not to mention it in the new district, because they do not like hearing it",
    "not present — the old man is the subject of this shot",
    "golden hour backlight, long shadows",
    "From 00:00.5, the old man speaks in a low voice in three-quarter back view, his head turning slightly as if checking whether anyone is around. From 00:04.0, he shifts the woven bag on his shoulder, ready to leave. From 00:06.0, he turns and walks out of frame; the camera holds on the empty scrap corner in the golden light",
    "low voices, the woven bag shifting on cloth, wind, distant traffic",
)

P["s23"] = (
    "the machine at night in <Picture 1>",
    "him crouched beside the machine in three-quarter side view, head lowered, one hand reaching down and out of focus, a weak glow just rising onto his lower face",
    "he crouches by the machine, his hand works out of focus below the frame, and a weak warm light rises onto his face",
    "fully_preserved — face, glasses, plaid shirt retained",
    "warm amber street lamp as the main light source, plus a weak glow rising from below",
    "From 00:00.0, he crouches in three-quarter side view, head lowered, one hand down and out of focus below the frame edge. From 00:02.5, a weak warm glow begins to rise and light his lower face, the rim of his glasses and his jaw; nothing else about the frame changes. From 00:05.0, he stays exactly that still, breathing slowly; the camera holds on his face and the rising glow. No mechanism and no socket are visible",
    "quiet night alley, a warm sodium lamp humming, a faint click from below",
)

P["s14"] = (
    "a scrap-collection corner in an old-town alley in <Picture 1>: a hill of machine shells, sheet metal, a half-dismantled fridge and stacked monitors, a torn plastic canopy overhead",
    "he sits on the ground beside the pile of scrap, doing nothing, one knee raised, hands resting on it, a shaft of afternoon sun on his shoes",
    "he simply sits there doing nothing, then his idle hand reaches over and picks at the rust on the machine beside him",
    "fully_preserved — face, glasses, plaid shirt and seated posture all retained",
    "warm afternoon light through a hole in the plastic canopy, dust in the beam",
    "From 00:00.0 to 00:04.0, he sits still beside the scrap pile, hunched slightly, hands on his knee, one fly circling in the air; only tiny movements: a slow blink, a shift of weight, one foot scraping dust off the other shoe. From 00:04.0 to 00:07.0, a shaft of sunlight through the canopy hole stays fixed on his shoe, dust drifting through it. From 00:07.0, his idle hand slowly reaches sideways and begins to pick at the flaking rust on the machine next to him, flakes dropping; the handheld camera drifts a little closer on his hand",
    "distant old-town street ambience, a bicycle bell far away, wind moving the plastic canopy, a faint fly buzzing",
)

P["s17"] = (
    "the scrap-collection corner in <Picture 1> and the rusted machine in <Picture 1>, with its screen glowing a year-2026-era interface",
    "him crouched in front of the rusted machine, its screen lighting his face from below, expression blank and still, dust in the air",
    "he crouches motionless in front of the freshly-revived machine, its year-2026 interface glowing on his face; he does not react, only looks",
    "fully_preserved — face, glasses, plaid shirt and crouched posture all retained",
    "screen glow from below mixed with warm late-afternoon light",
    "From 00:00.0 to 00:04.0, he stays crouched without moving, the machine's old interface throwing a soft light onto his glasses and cheekbones; dust drifts past the beam. From 00:04.0 to 00:06.5, his eyes move slightly across the screen but his expression stays blank; he does not smile and does not frown. From 00:06.5, he exhales once, his shoulders dropping a few millimetres; the handheld camera holds steady on his face",
    "quiet scrap-yard silence, a low electrical hum from the machine, distant street ambience",
)

P["s21"] = (
    "the alley mouth in <Picture 1>, scrap and old walls at dusk, warm orange streetlight just coming on",
    "him squatting at the alley mouth eating dry rations, and beside him a thin young man squatting with a small white pump box clipped to his waist and a thin tube against his abdomen",
    "the two squat side by side; the young man stares at the food in his hand and asks about it, then says that only three kinds of people in the city still eat",
    "fully_preserved — his face, glasses and plaid shirt retained; the young man is a separate character",
    "warm orange sodium streetlight at dusk",
    "From 00:00.5, he chews the dry rations slowly; beside him the young man stares at the food for a long beat without speaking. From 00:02.4, the young man speaks and taps the small white box on his waist with one finger. From 00:05.5, he answers without turning his head and keeps chewing. From 00:08.0, the young man laughs briefly and speaks again; he does not answer, just keeps eating; the handheld camera holds on both of them in the dusk",
    "dusk street ambience, distant traffic, a dog barking far off, the faint hum of the young man's pump box",
)

P["s22"] = (
    "the old-town alley in <Picture 1>, scrap piles along the walls, warm amber streetlight",
    "him walking in the alley, stopping mid-step, one hand pushed into his trouser pocket, body turned slightly",
    "he walks two steps, stops, reaches into his pocket and touches something, then turns and walks back",
    "fully_preserved — face, glasses, plaid shirt retained",
    "warm amber street lamp as the main light source illuminating the lane",
    "From 00:00.0 to 00:03.0, he walks forward through the lamp-lit alley, hands at his sides, the camera tracking beside him. From 00:03.0 to 00:05.4, he stops mid-step; his right hand slides into his trouser pocket and stays there, fingers moving as if touching something small. From 00:05.4, he stands still for a beat, looks back over his shoulder toward where he came from, then turns his body and starts walking back the way he came; the camera follows the turn",
    "quiet night alley ambience, a warm sodium lamp buzzing faintly, distant traffic, wind in the scrap piles",
)

P["s24"] = (
    "the dark alley in <Picture 1> with a warm amber street lamp behind him",
    "an extreme close-up of a hand holding an old smartphone whose screen has just lit up with an old year-2026 interface, showing a battery indicator reading 2%",
    "the old phone screen lights up in his hand showing 2% battery; he stares at it without moving",
    "partially_preserved — only his hand and the lower half of his face appear in this close-up",
    "the phone screen as the brightest light source, warm amber ambience",
    "From 00:00.0, the old phone screen flickers on in his hand; a year-2026 interface appears with a battery icon reading 2%, and the screen light rises onto his cheekbones and glasses. From 00:02.5, the glow steadies; his thumb does not move and he does not speak. From 00:05.0, his breathing slows and he keeps staring at the 2% icon; the camera holds absolutely still on the screen and his face",
    "night ambience, a faint sodium lamp hum, no music",
)

P["s25"] = (
    "the scrap pile and the rusted machine in <Picture 1> at night, warm amber lamp light",
    "him crouched in front of the rusted machine, lifting his head toward its screen as it flickers once more",
    "the machine's screen flickers once more; he lifts his head toward it and looks up",
    "fully_preserved — face, glasses, plaid shirt retained",
    "warm amber lamp light plus the machine screen's light",
    "From 00:00.0, he stays crouched, head down. From 00:02.0, the machine's screen flickers once — a soft electrical change — and the light catches his cheek. From 00:03.4, he lifts his head slowly and looks up toward the screen, his profile lit from two directions; his expression does not change. From 00:05.5, he holds that upward gaze; the camera holds still, then begins to creep a few centimetres closer as the shot ends",
    "night scrap-yard ambience, the machine's low electrical hum, one soft click as the screen flickers, distant traffic",
)


def h3_prompt(shot):
    scene, first, summ, ret1, light, action, sound = P[shot]
    return f"""subject_definitions:
<Subject 1> is the Chinese man defined by <Picture 2> (character sheet) and <Picture 3> (full-body front view): a lean man around 30, short messy black hair, old black-frame glasses with a scratched left lens and a taped temple, a faded plaid shirt with a frayed collar, dark work pants, oil-stained fingernails.
<Subject 2> is {scene}.
<Picture 1> is the first frame of [Shot 1]: {first}.

summary:
[keyframe completion + reference generation] The target video starts from <Picture 1> as its exact first frame: {summ}. <Picture 2> and <Picture 3> define <Subject 1>'s identity and clothing only.

retention_analysis:
<Subject 1> (appears in [Shot 1]): {ret1}.
<Subject 2> (appears in [Shot 1]): fully_preserved — the setting is retained exactly as in <Picture 1>.
<Picture 1> ([Shot 1] first frame): fully_preserved — the video opens on this exact frame and develops forward from it.

detailed_description:
{V} with {light}, handheld micro-shake, shallow depth of field, floating dust, framed tall so the subject stacks vertically in the narrow frame.
[Shot 1] The shot begins from <Picture 1>: {action}. No dialogue.

overall_soundscape: {sound}.

non_diegetic_music: N/A"""


def upload(path, name):
    boundary = "----wb" + uuid.uuid4().hex
    data = Path(path).read_bytes()
    ct = mimetypes.guess_type(str(path))[0] or "image/png"
    b = b""
    b += ("--%s\r\nContent-Disposition: form-data; name=\"image\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
          % (boundary, name, ct)).encode("utf-8")
    b += data
    b += ("\r\n--%s\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--%s--\r\n"
          % (boundary, boundary)).encode("utf-8")
    req = urllib.request.Request(HOST + "/upload/image", data=b,
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return json.load(urllib.request.urlopen(req, timeout=300))["name"]


def build(prompt, first_img, seed, prefix, frames):
    return {
        "119": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_video_vae_fp16.safetensors"}},
        "120": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax\\minimax_h3_audio_vae_fp32.safetensors"}},
        "128": {"class_type": "CLIPLoader", "inputs": {"clip_name": "minimax\\qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "151": {"class_type": "DiffusionModelLoaderKJ", "inputs": {"model_name": "minimax\\minimax_h3_ref2va_pruned_int8_convrot.safetensors", "weight_dtype": "default", "compute_dtype": "default", "patch_cublaslinear": False, "sage_attention": "auto", "enable_fp16_accumulation": True}},
        "137": {"class_type": "LoadImage", "inputs": {"image": first_img}},
        "139": {"class_type": "LoadImage", "inputs": {"image": "h3_ly_card.png"}},
        "145": {"class_type": "LoadImage", "inputs": {"image": "h3_ly_front.png"}},
        "136": {"class_type": "MiniMaxH3ReferenceToVideo",
                "inputs": {"clip": ["128", 0], "vae": ["119", 0], "audio_vae": ["120", 0],
                           "prompt": prompt, "width": 480, "height": 832, "length": frames,
                           "ref_image_size": "match",
                           "ref_images": [{"ref_image": ["137", 0]}, {"ref_image": ["139", 0]}, {"ref_image": ["145", 0]}]}},
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


def fetch(url, out, tries=4):
    """带重试的下载（ComfyUI 连接会抖动，一次失败不该毁掉整批）"""
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=900) as f, open(out, "wb") as o:
                o.write(f.read())
            return True
        except Exception as e:
            print("     下载失败(第%d/%d次): %s" % (k + 1, tries, e), flush=True)
            time.sleep(10)
    return False


def gen(shot):
    fname, cname, frames = SHOTS[shot]
    src = FRAME_DIR / fname
    if not src.exists():
        print("[%s] 首帧缺失 %s" % (shot, fname)); return
    out = OUT_DIR / ("%s_%s.mp4" % (shot, cname))
    if out.exists() and out.stat().st_size > 50_000:
        print("[%s] 已存在，跳过" % shot); return
    first = upload(src, "h3_%s_first.png" % shot)
    prompt = h3_prompt(shot)
    seed = 2026091200 + int(shot[1:])
    w = build(prompt, first, seed, "h3/ep01_%s" % shot, frames)
    req = urllib.request.Request(HOST + "/prompt", data=json.dumps({"prompt": w}).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        print("[%s] 提交失败: %s" % (shot, e.read().decode("utf-8", errors="replace")[:800])); return
    pid = r["prompt_id"]
    print("[%s] 提交 pid=%s frames=%d" % (shot, pid, frames), flush=True)
    while True:
        time.sleep(10)
        try:
            h = json.load(urllib.request.urlopen(HOST + "/history/" + pid, timeout=20))
        except Exception:
            continue
        if pid in h:
            st = h[pid].get("status", {}).get("status_str")
            if st == "error":
                for m in h[pid]["status"].get("messages", []):
                    if m[0] == "execution_error":
                        print("[%s] 执行错误 node=%s: %s" % (shot, m[1].get("node_type"), str(m[1].get("exception_message"))[:400]))
                return
            got = False
            for node, v in h[pid].get("outputs", {}).items():
                for key in ("videos", "gifs", "images"):
                    for it in v.get(key, []) or []:
                        fn = it.get("filename")
                        if not fn:
                            continue
                        q = "/view?filename=%s&subfolder=%s&type=output" % (urllib.request.quote(fn), urllib.request.quote(it.get("subfolder", "")))
                        OUT_DIR.mkdir(parents=True, exist_ok=True)
                        if fetch(HOST + q, out):
                            print("[%s] OK %.0fs -> %s (%.1f MB)" % (shot, time.time() - t0, out.name, out.stat().st_size / 1e6), flush=True)
                            got = True
                        else:
                            # 下载彻底失败：记录 pid，便于事后用 /view 单独取回
                            fp = OUT_DIR / "_待取回.json"
                            rec = {}
                            if fp.exists():
                                try: rec = json.loads(fp.read_text(encoding="utf-8"))
                                except Exception: rec = {}
                            rec[shot] = {"pid": pid, "filename": fn, "subfolder": it.get("subfolder", "")}
                            fp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                            print("[%s] 生成成功但下载失败，已记录到 _待取回.json（pid=%s）" % (shot, pid), flush=True)
            if not got:
                print("[%s] 完成但未取到视频产物: %s" % (shot, json.dumps(h[pid].get("outputs", {}), ensure_ascii=False)[:300]))
            return


if __name__ == "__main__":
    # 先上传角色卡与全身正面（<Picture 2> / <Picture 3>），一次即可
    n1 = upload(CARD, "h3_ly_card.png")
    n2 = upload(FRONT, "h3_ly_front.png") if FRONT.exists() else None
    print("角色参考已上传:", n1, n2, flush=True)
    args = sys.argv[1:] or ["s01"]
    targets = list(SHOTS.keys()) if args == ["all"] else args
    ok, fail = [], []
    for s in targets:
        try:
            gen(s)
            ok.append(s)
        except Exception as e:
            # 单镜异常不再终止整批
            print("[%s] 异常、跳过: %s: %s" % (s, type(e).__name__, e), flush=True)
            fail.append(s)
    print("done. 尝试 %d 镜 | 异常 %d 镜%s" % (len(targets), len(fail), (" -> " + ",".join(fail)) if fail else ""))

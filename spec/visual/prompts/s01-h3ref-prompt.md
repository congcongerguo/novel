# ep01 s01 · H3 Ref2VA 六段提示词（h3-prompt-writing skill 规范）

> 参考图顺序：<Picture 1>=h3_s01_first.png（首帧锚点）/ <Picture 2>=h3_luyuan_card.png（角色卡）/ <Picture 3>=h3_luyuan_front.png（全身正面）
> 输出：480x832 竖屏 · 121 帧 @24fps（约 5 秒）· ref_image_size=match
> 工作流：099.minimaxH3视频生成/ep01_s01_H3Ref.json

```text
subject_definitions:
<Subject 1> is the 32-year-old Chinese man defined by <Picture 2> (character sheet) and <Picture 3> (full-body front view): slightly heavyset build, short messy black hair, old black-frame glasses, faded plaid shirt with a frayed collar, dark work pants, and rough calloused hands with short clean nails.
<Subject 2> is the worn interior wall in <Picture 1>, with an old round white three-hole socket and a plastic-sheeted window leaking warm morning sunlight with floating dust.
<Picture 1> is the first frame of [Shot 1]: an extreme close-up of a rough hand pressing a worn grey two-pin plug toward the round socket, its flat pins misaligned with the round holes.

summary:
[keyframe completion + reference generation] The target video starts from <Picture 1> as its exact first frame: <Subject 1>'s hand tries to force the old two-pin plug into the round socket on <Subject 2>, fails twice, and finally hangs in mid-air between retries. Only the hand and shirt cuff of <Subject 1> appear on screen; his face never enters the frame. <Picture 2> and <Picture 3> define <Subject 1>'s identity and clothing only.

retention_analysis:
<Subject 1> (appears in [Shot 1], hand and cuff only): partially_preserved - only his hand, wrist and plaid shirt cuff are visible; face, glasses and full body stay off-frame.
<Subject 2> (appears in [Shot 1]): fully_preserved - the wall texture, the round three-hole socket and the plastic-sheet window are retained exactly as in <Picture 1>.
<Picture 1> ([Shot 1] first frame): fully_preserved - the video opens on this exact frame and develops forward from it.

detailed_description:
The target video is a photorealistic documentary-style vertical shot with warm morning light, handheld micro-shake, shallow depth of field and floating dust in the light beam.
[Shot 1] The shot begins from <Picture 1>: an extreme close-up of the rough hand of <Subject 1>, short clean nails and worn skin creases, gripping a grey two-pin plug with polished copper prongs, pressing it toward the round white three-hole socket on <Subject 2>. Warm sunlight leaks through the plastic-sheet window on the right, and dust motes drift in the beam. From 00:00.5 to 00:01.8, he pushes the plug firmly against the socket; the flat prongs catch the ceramic rim, scrape with a dry scratching sound, and slip off to the side. From 00:01.8 to 00:03.2, he rotates his wrist to try another angle and presses again; the prongs slide off once more, and his thumb rubs over the polished copper prongs as if checking them. From 00:03.2 to 00:05.0, he pulls the plug a few centimeters away from the wall and holds it in mid-air between the socket and the window light; the handheld camera dips slightly downward following his hand and settles on the gap between the plug and the socket. No face appears; only the frayed plaid shirt cuff of <Subject 1> is visible at the frame edge. No dialogue.

overall_soundscape: Quiet room tone with a faint electrical hum; occasional wind pressing the plastic-sheet window; a dry ceramic scraping sound each time the prongs slip; distant low traffic rumble from outside.

non_diegetic_music: N/A
```

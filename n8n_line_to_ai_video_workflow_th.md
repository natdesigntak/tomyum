# n8n Workflow: รับข้อมูลจาก LINE แล้วสร้างคลิปวิดีโออัตโนมัติด้วย AI (Google + Suno)

เอกสารนี้ออกแบบสำหรับ `n8n.natdesign.cloud` โดยมีเป้าหมายคือ:
- รับข้อมูลจาก LINE
- จำแนกประเภทงานสร้างคลิป 3 แบบ
- เรียก AI ที่เหมาะสมเพื่อสร้างภาพ/แอนิเมชัน/เสียง/เพลง
- รวมไฟล์ทั้งหมดเป็นวิดีโอสำเร็จรูปอัตโนมัติ

---

## 1) โครงสร้างระบบ (แนะนำให้ทำง่ายและเสถียรก่อน)

เพื่อให้ทำได้เร็วและดูแลง่าย แนะนำ **2-phase workflow** แทน one-shot ใหญ่ก้อนเดียว:

1. **Workflow A: Intake + Validate + Queue**
   - รับ webhook จาก LINE
   - แยกประเภทงาน + ตรวจข้อมูลครบไหม
   - เก็บไฟล์/เมตาดาต้าลง Storage + DB
   - ส่งงานเข้าคิว (เช่น Redis queue / n8n Execute Workflow)

2. **Workflow B: Render Pipeline (Async Worker)**
   - ดึงงานจากคิว
   - สร้าง script/storyboard
   - สร้างภาพฉาก + ภาพเคลื่อนไหว + เสียงพากย์ + เพลง
   - Render final video ด้วย FFmpeg
   - ส่งลิงก์ผลลัพธ์กลับ LINE

> ข้อดี: ถ้างานเรนเดอร์นานจะไม่ timeout webhook จาก LINE และ retry งานบางขั้นตอนได้ง่าย

---

## 2) ประเภทข้อมูลขาเข้า (LINE)

## Type 1: รีวิวสินค้า
รับข้อมูล:
- รูปสินค้า 1..N ภาพ
- รายละเอียดสินค้า (จุดเด่น, ราคา, กลุ่มเป้าหมาย)

Payload ตัวอย่าง:
```json
{
  "jobType": "product_review",
  "productImages": ["line_file_id_1", "line_file_id_2"],
  "productDetail": "หูฟังไร้สาย ANC แบต 30 ชม. ราคา 1,990 บาท",
  "tone": "น่าเชื่อถือ กระชับ",
  "durationSec": 45
}
```

## Type 2: ละครสั้น
รับข้อมูล:
- ภาพตัวละครหลัก
- ภาพตัวละครรอง
- ภาพตัวละครประกอบ
- บทคร่าวๆ

Payload ตัวอย่าง:
```json
{
  "jobType": "short_drama",
  "mainCharacterImages": ["line_file_id_a"],
  "supportCharacterImages": ["line_file_id_b"],
  "extraCharacterImages": ["line_file_id_c", "line_file_id_d"],
  "storyBrief": "เพื่อนสนิทเข้าใจผิดกัน แล้วกลับมาคืนดี",
  "style": "ดราม่าอบอุ่น",
  "durationSec": 60
}
```

## Type 3: บทสัมภาษณ์
รับข้อมูล:
- ภาพผู้สัมภาษณ์
- ภาพผู้ถูกสัมภาษณ์
- หัวข้อเรื่อง
- รายละเอียดคร่าวๆ

Payload ตัวอย่าง:
```json
{
  "jobType": "interview",
  "hostImages": ["line_file_id_h1"],
  "guestImages": ["line_file_id_g1"],
  "topic": "ธุรกิจร้านกาแฟยุค AI",
  "brief": "พูดถึงการใช้ AI ลดต้นทุนและเพิ่มยอดขาย",
  "durationSec": 50
}
```

---

## 3) Mapping AI ตามงาน (แนะนำ)

1. **เขียนสคริปต์ + Shot list**
   - ใช้ LLM (เช่น Gemini / GPT) เพื่อสร้าง:
     - Hook
     - Scene-by-scene script
     - Voice-over script
     - Subtitle text

2. **สร้างภาพประกอบฉาก**
   - ใช้ Google image generation model
   - Prompt จาก script + character consistency tokens

3. **สร้างภาพเคลื่อนไหว/วิดีโอช็อต**
   - ใช้ Google Flow / Veo pipeline (ตามที่ทีมคุณเข้าถึงได้)
   - Input: keyframes + motion prompt + duration ต่อช็อต

4. **เสียงพากย์ + Dialogue**
   - ใช้ TTS (Google Cloud TTS หรือ Gemini TTS)
   - แยก track ตามตัวละคร (ละคร/สัมภาษณ์)

5. **เพลงประกอบ**
   - ใช้ Suno API (หรือบริการเพลงที่รองรับเชิงพาณิชย์ตามสิทธิ์ใช้งานของคุณ)
   - สร้าง BGM ตาม mood: upbeat / dramatic / corporate

6. **SFX**
   - ใช้คลัง SFX หรือโมเดลสร้างเสียง

7. **รวมตัดต่ออัตโนมัติ**
   - FFmpeg compose:
     - concat video shots
     - mix voice + bgm + sfx
     - auto ducking bgm เมื่อมีเสียงพูด
     - burn subtitle

---

## 4) โหนด n8n ที่ควรใช้ (Blueprint)

## Workflow A: Intake
1. **Webhook (LINE callback)**
2. **Function: Parse Event**
3. **IF: jobType detected?**
4. **HTTP Request: Download LINE media**
5. **S3/Cloud Storage Upload**
6. **Function: Validate Required Fields**
7. **IF: valid?**
   - no -> LINE Reply: แจ้งข้อมูลไม่ครบ
   - yes -> DB Insert `jobs` + Execute Workflow (B)
8. **LINE Reply: รับงานแล้ว + job_id**

## Workflow B: Render
1. **Execute Workflow Trigger / Queue Trigger**
2. **DB Read Job Detail**
3. **Switch by `jobType`**
   - product_review
   - short_drama
   - interview
4. **LLM Script Generator**
5. **Split in Batches (shots)**
6. **HTTP Request: Generate scene images/videos**
7. **HTTP Request: TTS per line**
8. **HTTP Request: Suno music generation**
9. **Function: Build FFmpeg timeline JSON**
10. **Execute Command / Worker API: Render FFmpeg**
11. **Upload final.mp4**
12. **LINE Push Message: ส่งลิงก์/ไฟล์วิดีโอ**
13. **Update DB status = done/failed**

---

## 5) Prompt Template (สั้น ใช้งานจริง)

## Product Review Prompt
- Input: product detail + target audience + duration
- Output schema:
  - opening_hook
  - scenes[]: {visual_prompt, voice_text, subtitle, sec}
  - cta

## Short Drama Prompt
- Input: character cards + story brief
- Output schema:
  - character_voice_profile[]
  - scenes[] (dialogue + emotion + camera)
  - ending_message

## Interview Prompt
- Input: host card + guest card + topic + brief
- Output schema:
  - intro
  - qa_pairs[]
  - summary

---

## 6) Data Model ที่ควรมี

Table `jobs`
- `job_id`
- `line_user_id`
- `job_type`
- `input_json`
- `status` (queued|processing|done|failed)
- `progress` (0..100)
- `result_url`
- `error_message`
- `created_at`

Table `job_assets`
- `job_id`
- `asset_type` (image|video|voice|music|sfx|subtitle)
- `source`
- `url`
- `meta_json`

---

## 7) วิธีที่ง่ายกว่า (แนะนำเริ่มต้น MVP)

ถ้าต้องการ go-live เร็ว ให้ลดความซับซ้อนก่อน:

1. จำกัดวิดีโอ 30–45 วินาที
2. ใช้ template ตายตัว 5–7 ฉาก
3. ใช้ภาพนิ่ง + pan/zoom (Ken Burns) ก่อน video generation เต็มรูปแบบ
4. ใช้ TTS เสียงเดียวก่อน (ไม่แยกหลายตัวละคร)
5. เพลงใช้ 1 track ต่อคลิป
6. render ที่ 720p ก่อน แล้วค่อยขยาย

**ผลลัพธ์:** ลดต้นทุน, ลดเวลารอ, ลดจุดพัง, debug ง่ายขึ้นมาก

---

## 8) Error Handling สำคัญ

- Retry เฉพาะขั้นที่ idempotent (เช่น generate image)
- ใส่ timeout ต่อ API และ fallback model
- เก็บ intermediate artifacts ทุกขั้น
- ทำ dead-letter queue สำหรับงานล้มเหลวเกิน retry
- แจ้งสถานะผ่าน LINE: รับงานแล้ว / กำลังสร้าง / เสร็จแล้ว / ล้มเหลว

---

## 9) Security / Compliance Checklist

- ตรวจสิทธิ์การใช้ LINE media ก่อนดาวน์โหลด
- เข้ารหัส URL ไฟล์ชั่วคราว (signed URL)
- ลบไฟล์ชั่วคราวตาม retention
- ตรวจ license เพลง (โดยเฉพาะ Suno) ให้ตรง use case เชิงพาณิชย์
- ทำ content moderation เบื้องต้นก่อนเผยแพร่

---

## 10) ตัวอย่าง Routing Logic ใน n8n Function Node

```javascript
const body = $json;
if (!body.jobType) {
  return [{ json: { ok: false, error: 'missing jobType' } }];
}

const requiredMap = {
  product_review: ['productImages', 'productDetail'],
  short_drama: ['mainCharacterImages', 'supportCharacterImages', 'storyBrief'],
  interview: ['hostImages', 'guestImages', 'topic', 'brief'],
};

const req = requiredMap[body.jobType] || [];
const missing = req.filter((k) => !body[k] || (Array.isArray(body[k]) && body[k].length === 0));

return [{
  json: {
    ok: missing.length === 0,
    missing,
    jobType: body.jobType,
  }
}];
```

---

## 11) Roadmap การพัฒนา

- Sprint 1: Intake + Product Review MVP
- Sprint 2: Interview flow + subtitle burn-in
- Sprint 3: Short drama multi-character voices
- Sprint 4: Auto QA (lip sync quality, audio leveling, scene continuity)

หากต้องการ ผมสามารถช่วยต่อเป็น
1) โครงสร้าง n8n workflow แบบ import JSON,
2) ตัวอย่าง FFmpeg command ที่ใช้จริง,
3) ชุด prompt พร้อม output schema สำหรับแต่ละประเภทงาน.

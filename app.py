import streamlit as st
import anthropic
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import os

st.set_page_config(page_title="مولّد محتوى الألعاب", page_icon="🎮", layout="centered")

st.markdown("""
    <style>
    * { direction: rtl; text-align: right; }
    .stTextInput input { direction: rtl; text-align: right; }
    .stSelectbox div { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

CODES = {
    "GAME5":  {"type": "limited",   "limit": 10,  "price": "5 ريال"},
    "GAME39": {"type": "unlimited", "limit": 30,  "price": "39 ريال/شهر"},
    "GAME79": {"type": "unlimited", "limit": 100, "price": "79 ريال/شهر"},
}

if "remaining"       not in st.session_state: st.session_state.remaining = 0
if "code_type"       not in st.session_state: st.session_state.code_type = None
if "activated_code"  not in st.session_state: st.session_state.activated_code = None
if "daily_count"     not in st.session_state: st.session_state.daily_count = 0
if "last_date"       not in st.session_state: st.session_state.last_date = str(date.today())
if "last_result"     not in st.session_state: st.session_state.last_result = ""

if st.session_state.last_date != str(date.today()):
    st.session_state.daily_count = 0
    st.session_state.last_date   = str(date.today())

def add_text_to_image(image, text):
    img = image.copy().convert("RGBA")
    w, h = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([(0, h - 160), (w, h)], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img, overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    font_url = "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Bold.ttf"
    font_path = "Cairo-Bold.ttf"
    if not os.path.exists(font_path):
        r = requests.get(font_url)
        with open(font_path, "wb") as f:
            f.write(r.content)

    font_size = max(28, w // 18)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    max_chars = int(w / (font_size * 0.6))
    words = text.split()
    lines, line = [], ""
    for word in words:
        if len(line + " " + word) <= max_chars:
            line = (line + " " + word).strip()
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)

    y = h - 150
    for ln in lines[:3]:
        bbox = draw.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        draw.text((x+2, y+2), ln, font=font, fill=(0, 0, 0, 200))
        draw.text((x, y),   ln, font=font, fill=(255, 255, 255))
        y += font_size + 8

    return img

st.title("🎮 مولّد محتوى الألعاب")
st.markdown("عناوين وأوصاف يوتيوب + ثمبيل احترافي")
st.divider()

if st.session_state.activated_code is None:
    st.subheader("🔑 أدخل كود التفعيل")
    input_code = st.text_input("الكود", placeholder="مثال: GAME5")
    if st.button("✅ تفعيل", use_container_width=True):
        code = input_code.strip().upper()
        if code in CODES:
            st.session_state.activated_code = code
            st.session_state.code_type      = CODES[code]["type"]
            st.session_state.remaining      = CODES[code]["limit"]
            st.session_state.daily_count    = 0
            st.success(f"✅ تم التفعيل! باقة {CODES[code]['price']}")
            st.rerun()
        else:
            st.error("❌ الكود غير صحيح")
    st.divider()
    st.markdown("**باقة صغيرة** — 10 توليدات مقابل **5 ريال**")
    st.markdown("**باقة شهرية** — 30 توليد يومياً مقابل **39 ريال/شهر**")
    st.markdown("**باقة احترافية** — 100 توليد يومياً مقابل **79 ريال/شهر**")
    st.link_button("🛒 اشترِ الآن", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)
    
else:
    code_info = CODES[st.session_state.activated_code]
    if st.session_state.code_type == "limited":
        st.info(f"💳 رصيدك المتبقي: **{st.session_state.remaining} توليد**")
    else:
        daily_remaining = code_info["limit"] - st.session_state.daily_count
        st.info(f"💳 باقة شهرية | متبقي اليوم: **{daily_remaining} توليد**")

    tab1, tab2 = st.tabs(["✨ توليد المحتوى", "🖼️ صانع الثمبيل"])

    with tab1:
        video_title = st.text_input("📹 عنوان الفيديو أو فكرته")
        game_name   = st.text_input("🕹️ اسم اللعبة")
        dialect     = st.selectbox("🗣️ اللهجة",        ["خليجي", "سعودي", "فصحى", "مصري"])
        tone        = st.selectbox("🎭 نبرة المحتوى",   ["مثير وشيق", "مرح وخفيف", "احترافي", "تشويقي"])

        can_generate = (st.session_state.code_type == "limited" and st.session_state.remaining > 0) or \
                       (st.session_state.code_type == "unlimited" and st.session_state.daily_count < code_info["limit"])

        if st.button("✨ ولّد المحتوى", use_container_width=True, disabled=not can_generate):
            if not video_title or not game_name:
                st.error("أدخل عنوان الفيديو واسم اللعبة")
            else:
                with st.spinner("جاري التوليد..."):
                    try:
                        client   = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                        response = client.messages.create(
                            model="claude-haiku-4-5", max_tokens=800,
                            messages=[{"role": "user", "content": f"""أنت متخصص في كتابة محتوى يوتيوب للألعاب.
اكتب بـ{dialect} ونبرة {tone}.
فكرة الفيديو: {video_title}
اللعبة: {game_name}

**العنوان الرئيسي:**
[عنوان جذاب لا يتجاوز 70 حرف]

**3 عناوين بديلة:**
1. ...
2. ...
3. ...

**الوصف:**
[وصف جذاب 3-4 أسطر]

**الهاشتاقات:**
[15 هاشتاق مناسب]"""}]
                        )
                        result = response.content[0].text
                        st.session_state.last_result = result

                        if st.session_state.code_type == "limited":
                            st.session_state.remaining -= 1
                        else:
                            st.session_state.daily_count += 1

                        st.success("تم التوليد بنجاح! ✅")
                        st.markdown(result)
                        st.download_button("📋 حمّل النتيجة", result,
                                           file_name="youtube_content.txt", mime="text/plain")

                        if st.session_state.code_type == "limited" and st.session_state.remaining == 0:
                            st.warning("⚠️ نفد رصيدك!")
                            st.link_button("🛒 اشترِ الآن", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)
                    except Exception as e:
                        st.error(f"خطأ: {str(e)}")

        if not can_generate:
            st.warning("⚠️ نفد رصيدك أو وصلت للحد اليومي")
            st.link_button("🛒 اشترِ باقة جديدة", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)

    with tab2:
        st.markdown("### 🖼️ صانع الثمبيل")
        uploaded = st.file_uploader("ارفع صورة الثمبيل", type=["jpg", "jpeg", "png"])
        
        if st.session_state.last_result:
            default_text = st.session_state.last_result.split("\n")[1] if len(st.session_state.last_result.split("\n")) > 1 else ""
        else:
            default_text = ""

        thumb_text = st.text_input("✏️ النص الذي تريد على الثمبيل", value=default_text,
                                   placeholder="اكتب العنوان هنا أو استخدم العنوان المولّد")

        if uploaded and thumb_text:
            if st.button("🖼️ أنشئ الثمبيل", use_container_width=True):
                with st.spinner("جاري إنشاء الثمبيل..."):
                    try:
                        image  = Image.open(uploaded)
                        result = add_text_to_image(image, thumb_text)
                        buf    = io.BytesIO()
                        result.save(buf, format="PNG")
                        buf.seek(0)
                        st.image(result, caption="الثمبيل الجاهز", use_column_width=True)
                        st.download_button("⬇️ حمّل الثمبيل", buf,
                                           file_name="thumbnail.png", mime="image/png",
                                           use_container_width=True)
                    except Exception as e:
                        st.error(f"خطأ: {str(e)}")
        elif uploaded and not thumb_text:
            st.info("أدخل النص الذي تريده على الثمبيل")
        elif not uploaded:
            st.info("ارفع صورة أولاً لإنشاء الثمبيل")

    st.divider()
    if st.button("🔄 تغيير الكود", use_container_width=True):
        st.session_state.activated_code = None
        st.rerun()
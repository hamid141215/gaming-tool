import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
import anthropic
from openai import OpenAI
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re
import requests

st.set_page_config(page_title="مولّد محتوى الألعاب", page_icon="🎮", layout="wide")

st.markdown("""
    <style>
    * { direction: rtl; text-align: right; font-family: 'Segoe UI', sans-serif; }
    .stTextInput input { direction: rtl; text-align: right; }
    .stSelectbox div { direction: rtl; text-align: right; }
    .stSlider { direction: ltr; }
    div[data-testid="stHorizontalBlock"] { align-items: flex-start; }
    @media (max-width: 768px) {
        .stButton button { min-height: 50px; font-size: 16px; }
        .stSlider { padding: 8px 0; }
    }
    </style>
""", unsafe_allow_html=True)

CODES = {
    "GAME5":  {"type": "limited",   "limit": 10,  "price": "5 ريال"},
    "GAME39": {"type": "unlimited", "limit": 30,  "price": "39 ريال/شهر"},
    "GAME79": {"type": "unlimited", "limit": 100, "price": "79 ريال/شهر"},
}

FONTS = {
    "Amiri (كلاسيكي)": "Amiri-Bold.ttf",
    "Tajawal (حديث)":   "Tajawal-Bold.ttf",
    "Lateef (أنيق)":    "Lateef-Bold.ttf",
}

COLOR_PRESETS = {
    "⚡ أصفر":    ("#FFD700", "#000000"),
    "🔥 أبيض":    ("#FFFFFF", "#000000"),
    "💥 أحمر":    ("#FF3333", "#000000"),
    "🌊 أزرق":    ("#00CFFF", "#003366"),
    "💚 أخضر":    ("#39FF14", "#003300"),
    "🟠 برتقالي": ("#FF8C00", "#000000"),
}

if "remaining"      not in st.session_state: st.session_state.remaining = 0
if "code_type"      not in st.session_state: st.session_state.code_type = None
if "activated_code" not in st.session_state: st.session_state.activated_code = None
if "daily_count"    not in st.session_state: st.session_state.daily_count = 0
if "last_date"      not in st.session_state: st.session_state.last_date = str(date.today())
if "last_result"    not in st.session_state: st.session_state.last_result = ""
if "main_title"     not in st.session_state: st.session_state.main_title = ""
if "thumb_created"  not in st.session_state: st.session_state.thumb_created = False
if "uploaded_bytes" not in st.session_state: st.session_state.uploaded_bytes = None
if "text_color"     not in st.session_state: st.session_state.text_color = "#FFD700"
if "shadow_color"   not in st.session_state: st.session_state.shadow_color = "#000000"
if "font_name"      not in st.session_state: st.session_state.font_name = "Amiri (كلاسيكي)"
if "font_size"      not in st.session_state: st.session_state.font_size = 120
if "position"       not in st.session_state: st.session_state.position = "أسفل"
if "text_align"     not in st.session_state: st.session_state.text_align = "وسط"
if "bg_opacity"     not in st.session_state: st.session_state.bg_opacity = 0.0
if "thumb_text"     not in st.session_state: st.session_state.thumb_text = ""
if "thumb_mode"     not in st.session_state: st.session_state.thumb_mode = "ارفع صورة"

if st.session_state.last_date != str(date.today()):
    st.session_state.daily_count = 0
    st.session_state.last_date   = str(date.today())

BASE_DIR = os.path.dirname(__file__)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def add_text_to_image(image_bytes, text, font_name, font_size,
                      text_color, shadow_color, position,
                      bg_opacity, text_align):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    zone_h = font_size * 3 + 60
    if position == "أسفل":
        zone_y = h - zone_h
    elif position == "وسط":
        zone_y = (h - zone_h) // 2
    else:
        zone_y = 10

    if bg_opacity > 0:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        draw_ov.rectangle(
            [(0, zone_y), (w, zone_y + zone_h)],
            fill=(0, 0, 0, int(bg_opacity * 255))
        )
        img = Image.alpha_composite(img, overlay)

    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    font_file = FONTS.get(font_name, "Amiri-Bold.ttf")
    font_path = os.path.join(BASE_DIR, font_file)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default(size=font_size)

    max_chars = max(10, int(w / (font_size * 0.55)))
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) <= max_chars:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    lines = lines[:3]

    reshaped = [get_display(arabic_reshaper.reshape(ln)) for ln in lines]

    total_h = len(reshaped) * (font_size + 14)
    y = zone_y + max(0, (zone_h - total_h) // 2)
    tc = hex_to_rgb(text_color)
    sc = hex_to_rgb(shadow_color)
    border = max(3, font_size // 10)

    emoji_font_path = os.path.join(BASE_DIR, "NotoEmoji.ttf")
    try:
        emoji_font = ImageFont.truetype(emoji_font_path, font_size)
    except:
        emoji_font = None

    emoji_pattern = re.compile("[\U00010000-\U0010ffff\U00002600-\U000027BF]", flags=re.UNICODE)

    for ln in reshaped:
        try:
            bbox = draw.textbbox((0, 0), ln, font=font)
            tw = bbox[2] - bbox[0]
        except:
            tw = len(ln) * font_size // 2

        if text_align == "وسط":
            x = max(10, (w - tw) // 2)
        elif text_align == "يمين":
            x = max(10, w - tw - 20)
        else:
            x = 20

        for dx in range(-border, border + 1):
            for dy in range(-border, border + 1):
                if abs(dx) + abs(dy) <= border + 1:
                    draw.text((x+dx, y+dy), ln, font=font, fill=sc)

        cur_x = x
        for char in ln:
            if emoji_pattern.match(char) and emoji_font:
                draw.text((cur_x, y), char, font=emoji_font, fill=(255,255,255,255), embedded_color=True)
                try:
                    bbox = draw.textbbox((cur_x, y), char, font=emoji_font)
                    cur_x += bbox[2] - bbox[0]
                except:
                    cur_x += font_size
            else:
                draw.text((cur_x, y), char, font=font, fill=tc)
                try:
                    bbox = draw.textbbox((cur_x, y), char, font=font)
                    cur_x += bbox[2] - bbox[0]
                except:
                    cur_x += font_size // 2
        y += font_size + 14

    return img

def render_thumbnail():
    result = add_text_to_image(
        st.session_state.uploaded_bytes,
        st.session_state.thumb_text,
        st.session_state.font_name,
        st.session_state.font_size,
        st.session_state.text_color,
        st.session_state.shadow_color,
        st.session_state.position,
        st.session_state.bg_opacity,
        st.session_state.text_align
    )
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return result, buf

def generate_ai_image(game_name, extra_desc=""):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = (
        f"YouTube gaming thumbnail for {game_name}. "
        f"{extra_desc}. "
        "Close-up face with exaggerated expression, dramatic lighting, "
        "high contrast, vibrant colors, dark background, subject in center, "
        "sharp focus, 4K quality, viral style, cinematic, no text."
    )
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    img_bytes = requests.get(image_url).content
    return img_bytes

def extract_main_title(result):
    lines = result.split("\n")
    for i, ln in enumerate(lines):
        if "العنوان الرئيسي" in ln:
            for j in range(i+1, min(i+5, len(lines))):
                clean = lines[j].strip().replace("**","").replace("[","").replace("]","").replace("*","")
                if clean and len(clean) > 5:
                    return clean
    return ""

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
        dialect     = st.selectbox("🗣️ اللهجة",       ["خليجي", "سعودي", "فصحى", "مصري"])
        tone        = st.selectbox("🎭 نبرة المحتوى",  ["مثير وشيق", "مرح وخفيف", "احترافي", "تشويقي"])

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
                        st.session_state.main_title  = extract_main_title(result)

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

        if st.session_state.main_title:
            st.success(f"✅ العنوان المولّد: {st.session_state.main_title}")

        st.session_state.thumb_mode = st.radio(
            "اختر طريقة الصورة",
            ["ارفع صورة", "ولّد صورة بالذكاء الاصطناعي"],
            horizontal=True
        )

        if st.session_state.thumb_mode == "ارفع صورة":
            uploaded = st.file_uploader("ارفع صورة الثمبيل", type=["jpg","jpeg","png"])
            if uploaded:
                new_bytes = uploaded.read()
                if new_bytes != st.session_state.uploaded_bytes:
                    st.session_state.uploaded_bytes = new_bytes
                    st.session_state.thumb_created  = False

        else:
            ai_game = st.text_input("🎮 اسم اللعبة للصورة", placeholder="مثال: Valorant")
            ai_desc = st.text_input("✨ وصف إضافي (اختياري)", placeholder="مثال: لاعب يحتفل بالفوز")

            if st.button("🤖 ولّد صورة بالذكاء الاصطناعي", use_container_width=True):
                if not ai_game:
                    st.error("أدخل اسم اللعبة")
                else:
                    with st.spinner("جاري توليد الصورة... قد يستغرق 15-20 ثانية"):
                        try:
                            img_bytes = generate_ai_image(ai_game, ai_desc)
                            st.session_state.uploaded_bytes = img_bytes
                            st.session_state.thumb_created  = False
                            st.success("تم توليد الصورة! ✅")
                        except Exception as e:
                            st.error(f"خطأ في توليد الصورة: {str(e)}")

        default_text = st.session_state.main_title if st.session_state.main_title else ""
        thumb_text = st.text_input("✏️ النص على الثمبيل",
                                   value=default_text,
                                   placeholder="ولّد عنواناً أولاً أو اكتب نصاً هنا")
        st.session_state.thumb_text = thumb_text

        if st.session_state.uploaded_bytes and thumb_text and not st.session_state.thumb_created:
            if st.button("🖼️ أنشئ الثمبيل", use_container_width=True):
                st.session_state.thumb_created = True

        if st.session_state.thumb_created and st.session_state.uploaded_bytes and thumb_text:
            st.divider()
            left_col, right_col = st.columns([1, 1])

            with right_col:
                st.markdown("#### ⚙️ أدوات التعديل")

                st.session_state.font_name = st.selectbox(
                    "🔤 الخط", list(FONTS.keys()),
                    index=list(FONTS.keys()).index(st.session_state.font_name)
                )
                st.session_state.font_size = st.slider(
                    "📏 حجم الخط", 60, 300,
                    st.session_state.font_size, step=4
                )
                st.session_state.position = st.selectbox(
                    "📍 موضع النص", ["أسفل", "وسط", "أعلى"],
                    index=["أسفل", "وسط", "أعلى"].index(st.session_state.position)
                )
                st.session_state.text_align = st.selectbox(
                    "↔️ محاذاة", ["وسط", "يمين", "يسار"],
                    index=["وسط", "يمين", "يسار"].index(st.session_state.text_align)
                )
                st.session_state.bg_opacity = st.slider(
                    "🌫️ شفافية الخلفية", 0.0, 1.0,
                    st.session_state.bg_opacity, step=0.05
                )

                st.markdown("**🎨 ألوان جاهزة**")
                cols = st.columns(3)
                for i, (name, (tc, sc)) in enumerate(COLOR_PRESETS.items()):
                    with cols[i % 3]:
                        if st.button(name, use_container_width=True, key=f"color_{i}"):
                            st.session_state.text_color   = tc
                            st.session_state.shadow_color = sc

                st.markdown("**🖌️ لون مخصص**")
                c1, c2 = st.columns(2)
                with c1:
                    st.session_state.text_color = st.color_picker(
                        "النص", st.session_state.text_color
                    )
                with c2:
                    st.session_state.shadow_color = st.color_picker(
                        "الظل", st.session_state.shadow_color
                    )

            with left_col:
                st.markdown("#### 👁️ معاينة مباشرة")
                try:
                    result_img, buf = render_thumbnail()
                    st.image(result_img, use_column_width=True)
                    st.download_button(
                        "⬇️ حمّل الثمبيل الآن",
                        buf,
                        file_name="thumbnail.png",
                        mime="image/png",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")

            st.divider()
            if st.button("🔁 ابدأ من جديد", use_container_width=True):
                st.session_state.thumb_created  = False
                st.session_state.uploaded_bytes = None
                st.rerun()

        elif st.session_state.uploaded_bytes and not thumb_text:
            st.info("اكتب النص الذي تريده على الثمبيل")
        elif not st.session_state.uploaded_bytes:
            st.info("ارفع صورة أو ولّد صورة بالذكاء الاصطناعي أولاً")

    st.divider()
    if st.button("🔄 تغيير الكود", use_container_width=True):
        st.session_state.activated_code = None
        st.rerun()
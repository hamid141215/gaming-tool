import streamlit as st
import arabic_reshaper
from bidi.algorithm import get_display
import anthropic
from datetime import date
from PIL import Image, ImageDraw, ImageFont
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

if "remaining"      not in st.session_state: st.session_state.remaining = 0
if "code_type"      not in st.session_state: st.session_state.code_type = None
if "activated_code" not in st.session_state: st.session_state.activated_code = None
if "daily_count"    not in st.session_state: st.session_state.daily_count = 0
if "last_date"      not in st.session_state: st.session_state.last_date = str(date.today())
if "last_result"    not in st.session_state: st.session_state.last_result = ""
if "main_title"     not in st.session_state: st.session_state.main_title = ""
if "thumb_created"  not in st.session_state: st.session_state.thumb_created = False
if "uploaded_bytes" not in st.session_state: st.session_state.uploaded_bytes = None

if st.session_state.last_date != str(date.today()):
    st.session_state.daily_count = 0
    st.session_state.last_date   = str(date.today())

FONT_PATH = os.path.join(os.path.dirname(__file__), "Amiri-Bold.ttf")

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def add_text_to_image(image_bytes, text, font_size, text_color,
                      shadow_color, position, bg_opacity, text_align):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size

    zone_h = font_size * 3 + 60
    if position == "أسفل":
        zone_y = h - zone_h
    elif position == "وسط":
        zone_y = (h - zone_h) // 2
    else:
        zone_y = 10

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    draw_ov.rectangle(
        [(0, zone_y), (w, zone_y + zone_h)],
        fill=(0, 0, 0, int(bg_opacity * 255))
    )
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
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

    total_h = len(lines) * (font_size + 12)
    y = zone_y + max(0, (zone_h - total_h) // 2)
    tc = hex_to_rgb(text_color)
    sc = hex_to_rgb(shadow_color)

    for ln in lines:
ln = get_display(arabic_reshaper.reshape(ln))
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

        draw.text((x+2, y+2), ln, font=font, fill=sc)
        draw.text((x, y),     ln, font=font, fill=tc)
        y += font_size + 12

    return img

def extract_main_title(result):
    lines = result.split("\n")
    for i, ln in enumerate(lines):
        if "العنوان الرئيسي" in ln:
            for j in range(i+1, min(i+5, len(lines))):
                clean = lines[j].strip().replace("**","").replace("[","").replace("]","").replace("*","")
                if clean and len(clean) > 5:
                    return clean
    return ""

def render_thumbnail(image_bytes, text, font_size, text_color,
                     shadow_color, position, bg_opacity, text_align):
    result = add_text_to_image(image_bytes, text, font_size, text_color,
                               shadow_color, position, bg_opacity, text_align)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    buf.seek(0)
    return result, buf

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

        uploaded = st.file_uploader("ارفع صورة الثمبيل", type=["jpg","jpeg","png"])
        if uploaded:
            st.session_state.uploaded_bytes = uploaded.read()

        default_text = st.session_state.main_title if st.session_state.main_title else ""
        thumb_text = st.text_input("✏️ النص على الثمبيل",
                                   value=default_text,
                                   placeholder="ولّد عنواناً أولاً أو اكتب نصاً هنا")

        if st.session_state.uploaded_bytes and thumb_text:
            if not st.session_state.thumb_created:
                if st.button("🖼️ أنشئ الثمبيل", use_container_width=True):
                    st.session_state.thumb_created = True
                    st.rerun()

        if st.session_state.thumb_created and st.session_state.uploaded_bytes and thumb_text:
            st.divider()
            st.markdown("#### ⚙️ تعديل مباشر على الثمبيل")

            col1, col2 = st.columns(2)
            with col1:
                font_size  = st.slider("حجم الخط", 20, 120, 48, step=4)
                position   = st.selectbox("موضع النص", ["أسفل", "وسط", "أعلى"])
                text_align = st.selectbox("محاذاة النص", ["وسط", "يمين", "يسار"])
            with col2:
                text_color   = st.color_picker("لون النص",        "#FFFFFF")
                shadow_color = st.color_picker("لون الظل",        "#000000")
                bg_opacity   = st.slider("شفافية الخلفية", 0.0, 1.0, 0.7, step=0.05)

            try:
                result_img, buf = render_thumbnail(
                    st.session_state.uploaded_bytes,
                    thumb_text, font_size, text_color,
                    shadow_color, position, bg_opacity, text_align
                )
                st.image(result_img, caption="معاينة مباشرة", use_column_width=True)
                st.download_button("⬇️ حمّل الثمبيل", buf,
                                   file_name="thumbnail.png", mime="image/png",
                                   use_container_width=True)
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

            if st.button("🔁 ارفع صورة جديدة", use_container_width=True):
                st.session_state.thumb_created  = False
                st.session_state.uploaded_bytes = None
                st.rerun()

        elif st.session_state.uploaded_bytes and not thumb_text:
            st.info("ولّد عنواناً من التبويب الأول أو اكتب نصاً يدوياً")
        elif not st.session_state.uploaded_bytes:
            st.info("ارفع صورة أولاً لإنشاء الثمبيل")

    st.divider()
    if st.button("🔄 تغيير الكود", use_container_width=True):
        st.session_state.activated_code = None
        st.rerun()
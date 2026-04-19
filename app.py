import streamlit as st
import anthropic
from datetime import date

st.set_page_config(page_title="مولّد محتوى الألعاب", page_icon="🎮", layout="centered")

st.markdown("""
    <style>
    * { direction: rtl; text-align: right; }
    .stTextInput input { direction: rtl; text-align: right; }
    .stSelectbox div { direction: rtl; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# نظام الأكواد
CODES = {
    "GAME5":  {"type": "limited",   "limit": 10,  "price": "5 ريال"},
    "GAME29": {"type": "unlimited", "limit": 50,  "price": "29 ريال/شهر"},
}

# تهيئة الجلسة
if "remaining" not in st.session_state:
    st.session_state.remaining = 0
if "code_type" not in st.session_state:
    st.session_state.code_type = None
if "activated_code" not in st.session_state:
    st.session_state.activated_code = None
if "daily_count" not in st.session_state:
    st.session_state.daily_count = 0
if "last_date" not in st.session_state:
    st.session_state.last_date = str(date.today())

# إعادة ضبط العداد اليومي
if st.session_state.last_date != str(date.today()):
    st.session_state.daily_count = 0
    st.session_state.last_date = str(date.today())

st.title("🎮 مولّد عناوين وأوصاف يوتيوب للألعاب")
st.markdown("أداة ذكاء اصطناعي لمنشئي محتوى الألعاب السعوديين")
st.divider()

# واجهة تفعيل الكود
if st.session_state.activated_code is None:
    st.subheader("🔑 أدخل كود التفعيل")
    input_code = st.text_input("الكود", placeholder="مثال: GAME00")

    if st.button("✅ تفعيل", use_container_width=True):
        code = input_code.strip().upper()
        if code in CODES:
            st.session_state.activated_code = code
            st.session_state.code_type = CODES[code]["type"]
            st.session_state.remaining = CODES[code]["limit"]
            st.session_state.daily_count = 0
            st.success(f"✅ تم التفعيل! باقة {CODES[code]['price']}")
            st.rerun()
        else:
            st.error("❌ الكود غير صحيح — تحقق من الكود وحاول مجدداً")

    st.divider()
    st.markdown("### 🛒 احصل على كود تفعيل")
    st.markdown("**باقة صغيرة** — 10 توليدات مقابل **5 ريال**")
    st.markdown("**باقة شهرية** — توليدات يومية غير محدودة مقابل **29 ريال/شهر**")
    st.link_button("🛒 اشترِ الآن", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)

else:
    # عرض الرصيد
    code_info = CODES[st.session_state.activated_code]
    if st.session_state.code_type == "limited":
        st.info(f"💳 رصيدك المتبقي: **{st.session_state.remaining} توليد**")
    else:
        daily_remaining = code_info["limit"] - st.session_state.daily_count
        st.info(f"💳 باقة شهرية | متبقي اليوم: **{daily_remaining} توليد**")

    # نموذج التوليد
    video_title = st.text_input("📹 عنوان الفيديو أو فكرته")
    game_name   = st.text_input("🕹️ اسم اللعبة")
    dialect     = st.selectbox("🗣️ اللهجة", ["خليجي", "سعودي", "فصحى", "مصري"])
    tone        = st.selectbox("🎭 نبرة المحتوى", ["مثير وشيق", "مرح وخفيف", "احترافي", "تشويقي"])

    can_generate = False
    if st.session_state.code_type == "limited":
        can_generate = st.session_state.remaining > 0
    else:
        can_generate = st.session_state.daily_count < code_info["limit"]

    if st.button("✨ ولّد المحتوى", use_container_width=True, disabled=not can_generate):
        if not video_title or not game_name:
            st.error("أدخل عنوان الفيديو واسم اللعبة")
        else:
            with st.spinner("جاري التوليد..."):
                try:
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                    response = client.messages.create(
                        model="claude-haiku-4-5",
                        max_tokens=800,
                        messages=[{
                            "role": "user",
                            "content": f"""أنت متخصص في كتابة محتوى يوتيوب لمنشئي محتوى الألعاب.
اكتب بـ{dialect} ونبرة {tone}.

فكرة الفيديو: {video_title}
اللعبة: {game_name}

اكتب بالتنسيق التالي بالضبط:

**العنوان الرئيسي:**
[عنوان جذاب لا يتجاوز 70 حرف]

**3 عناوين بديلة:**
1. ...
2. ...
3. ...

**الوصف:**
[وصف جذاب 3-4 أسطر يشجع على المشاهدة]

**الهاشتاقات:**
[15 هاشتاق مناسب للألعاب والسوق السعودي]"""
                        }]
                    )

                    result = response.content[0].text

                    # تحديث الرصيد
                    if st.session_state.code_type == "limited":
                        st.session_state.remaining -= 1
                    else:
                        st.session_state.daily_count += 1

                    st.success("تم التوليد بنجاح! ✅")
                    st.markdown(result)

                    st.download_button(
                        "📋 حمّل النتيجة",
                        result,
                        file_name="youtube_content.txt",
                        mime="text/plain"
                    )

                    # تنبيه نفاد الرصيد
                    if st.session_state.code_type == "limited" and st.session_state.remaining == 0:
                        st.warning("⚠️ نفد رصيدك! اشترِ باقة جديدة للاستمرار.")
                        st.link_button("🛒 اشترِ الآن", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)

                except Exception as e:
                    st.error(f"خطأ: {str(e)}")

    if not can_generate:
        if st.session_state.code_type == "limited":
            st.warning("⚠️ نفد رصيدك!")
        else:
            st.warning("⚠️ وصلت للحد اليومي — يتجدد غداً")
        st.link_button("🛒 اشترِ باقة جديدة", "https://salla.sa/mawjatalsamt/category/lRlwoA", use_container_width=True)

    st.divider()
    if st.button("🔄 تغيير الكود", use_container_width=True):
        st.session_state.activated_code = None
        st.rerun()
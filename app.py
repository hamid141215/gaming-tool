import streamlit as st
import anthropic

st.set_page_config(page_title="مولّد محتوى الألعاب", page_icon="🎮", layout="centered")

st.title("🎮 مولّد عناوين وأوصاف يوتيوب للألعاب")
st.markdown("أداة ذكاء اصطناعي لمنشئي محتوى الألعاب السعوديين")

st.divider()

video_title = st.text_input("📹 عنوان الفيديو المؤقت أو فكرته")
game_name = st.text_input("🕹️ اسم اللعبة")
dialect = st.selectbox("🗣️ اللهجة", ["خليجي", "سعودي", "فصحى", "مصري"])
tone = st.selectbox("🎭 نبرة المحتوى", ["مثير وشيق", "مرح وخفيف", "احترافي", "تشويقي"])

if st.button("✨ ولّد المحتوى", use_container_width=True):
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
                st.success("تم التوليد بنجاح! ✅")
                st.markdown(result)

                st.download_button(
                    "📋 حمّل النتيجة",
                    result,
                    file_name="youtube_content.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"خطأ: {str(e)}")
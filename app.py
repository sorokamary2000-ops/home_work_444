import io
import urllib.parse
import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="AI Generator & Filters", layout="wide")


def generate_image(prompt):
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
        response = requests.get(url, timeout=45)
        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Помилка сервера ({response.status_code})"
    except requests.exceptions.Timeout:
        return None, "Сервер недоступний (таймаут)"
    except Exception as e:
        return None, f"Помилка при генерації: {e}"


st.title("AI Генератор зображень + Фільтри")
st.write(
    "Згенеруйте зображення за допомогою ШІ, а потім накладіть на нього бажаний фільтр!"
)

col_input, col_style = st.columns([2, 1])

with col_input:
    prompt = st.text_area(
        "Введіть опис зображення (Промпт):",
        placeholder="Наприклад: cute cat with a ball of yarn",
    )

STYLES = {
    "Без стилю": "",
    "Реалістичний": "high detail, photorealistic, natural lighting",
    "Акварель": "watercolor painting style, soft edges, pastel colors",
    "Мультяшний": "3D animated movie style, vibrant colors, friendly look",
    "Піксель-Арт": "pixel art style, 16-bit retro game aesthetic",
}

with col_style:
    style_choice = st.selectbox("Стиль ШІ", list(STYLES.keys()))

if st.button("Згенерувати зображення"):
    if not prompt.strip():
        st.warning("Будь ласка, введіть опис зображення!")
    else:
        style_text = STYLES[style_choice]
        final_prompt = f"{prompt}, {style_text}" if style_text else prompt

        with st.spinner("Нейромережа генерує зображення..."):
            image_bytes, error = generate_image(final_prompt)

        if error:
            st.error(f"Не вдалося згенерувати: {error}")
        elif image_bytes:
            st.session_state["raw_ai_image"] = image_bytes
            st.success("Зображення успішно згенеровано!")

if "raw_ai_image" in st.session_state:
    st.markdown("---")
    st.subheader("Редагування згенерованого зображення фільтрами")

    ai_img_pil = Image.open(io.BytesIO(st.session_state["raw_ai_image"]))
    img_array = np.array(ai_img_pil)

    filter_option = st.selectbox(
        "Оберіть ефект для згенерованого фото:",
        [
            "Оригінал (без фільтрів)",
            "Чорно-біле (ЧБ)",
            "Розмиття (Blur)",
            "Збільшити яскравість",
            "Інверсія кольорів",
        ],
    )

    processed_img = img_array.copy()

    if filter_option == "Чорно-біле (ЧБ)":
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        processed_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    elif filter_option == "Розмиття (Blur)":
        processed_img = cv2.GaussianBlur(img_array, (15, 15), 0)
    elif filter_option == "Збільшити яскравість":
        processed_img = cv2.convertScaleAbs(img_array, alpha=1.0, beta=50)
    elif filter_option == "Інверсія кольорів":
        processed_img = 255 - img_array

    col_orig, col_filt = st.columns(2)

    with col_orig:
        st.caption("Оригінал від ШІ")
        st.image(img_array, use_container_width=True)

    with col_filt:
        st.caption(f"З обробкою: {filter_option}")
        st.image(processed_img, use_container_width=True)

        result_pil = Image.fromarray(processed_img)
        buf = io.BytesIO()
        result_pil.save(buf, format="PNG")
        byte_im = buf.getvalue()

        st.download_button(
            label="Скачати оброблене фото",
            data=byte_im,
            file_name="ai_filtered_result.png",
            mime="image/png",
        )
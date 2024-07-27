import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import json
import base64
from PIL import Image
import io
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# Load content from JSON files
with open('data/home_content.json', 'r') as f:
    home_content = json.load(f)

with open('data/client_personas.json', 'r') as f:
    client_personas_data = json.load(f)

# Database setup
conn = sqlite3.connect('responses.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS responses
             (mcq1 TEXT, mcq2 TEXT, mcq3 TEXT, txt1 TEXT, txt2)''')
conn.commit()

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Home'
if 'selected_persona' not in st.session_state:
    st.session_state.selected_persona = None

# Load image function
def load_image(image_path):
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        st.error(f"Image file {image_path} not found.")
        return None

# Define a function for each page
def home():
    st.title(home_content["title"])
    st.subheader(home_content["subtitle"])
    st.write(home_content["welcome"])
    st.markdown(home_content["intro"])
    
    st.subheader(home_content["key_features"]["title"])
    for item in home_content["key_features"]["items"]:
        st.markdown(f"* {item}")
    
    st.subheader(home_content["value"]["title"])
    for item in home_content["value"]["items"]:
        st.markdown(f"* {item}")
    
    st.subheader(home_content["why_choose"]["title"])
    for item in home_content["why_choose"]["items"]:
        st.markdown(f"* {item}")

def Questionnaire():
    st.title("Questionnaire Page")
    st.subheader("Hello Advisor, Please answer the following Questions.")
    st.subheader("Multiple Choice Questions")
    mcq1 = st.radio("1. How many years of experience do you have in retirement planning?", ("Less than 1 year", "1-5 years", "5-10 years", "More than 10 years"))
    mcq2 = st.radio("2. What is your primary area of expertise?", ("Investment Management", "Tax Planning", "Estate Planning Comprehensive", "Retirement Planning"))
    mcq3 = st.radio("3. What types of clients do you typically work with", ("Individuals", "Families", "Small Businesses", "Corporations"))

    st.subheader("Text Box Questions")
    txt1 = st.text_input("4. Can you describe a successful retirement plan you created for a client and the key strategies you used?")
    txt2 = st.text_input("5. What motivates you to help clients with their retirement planning?")

    if st.button("Submit"):
        # Store the responses in the database
        c.execute("INSERT INTO responses (mcq1, mcq2, mcq3, txt1, txt2) VALUES (?, ?, ?, ?, ?)",
                  (mcq1, mcq2, mcq3, txt1, txt2))
        conn.commit()
        st.success("Your responses have been submitted successfully!")

def contact():
    st.title("Contact Page")
    st.write("This is the contact page.")

def client_personas():
    st.title("Client Personas")
    st.write("Select a client persona to simulate a retirement planning conversation.")

    # Calculate the height of the persona section
    num_personas = len(client_personas_data['personas'])
    rows = (num_personas + 2) // 3  # Calculate number of rows needed for 3 columns
    total_height = rows * 500  # Adjust height per row as needed

    persona_html = '''
    <style>
    .persona-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 50px;
        padding: 20px;
        width: 100%;
        box-sizing: border-box;
    }
    .persona-card {
        width: 100%;
        text-align: center;
        border-radius: 8px;
        padding: 15px;
        transition: all 0.3s ease;
        background: linear-gradient(145deg, rgba(0, 0, 0, 0.8), rgba(50, 50, 50, 0.8));
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
        display: flex;
        flex-direction: column;
    }
    .persona-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.5);
        background: linear-gradient(145deg, rgba(0, 0, 0, 1), rgba(50, 50, 50, 1));
    }
    .persona-card .image-container {
        width: 100%;
        padding-top: 100%;
        position: relative;
        overflow: hidden;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .persona-card .image-container img {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: all 0.3s ease;
    }
    .persona-card:hover .image-container img {
        transform: scale(1.05);
    }
    .persona-card h3 {
        margin-top: 8px;
        margin-bottom: 8px;
        font-weight: bold;
        color: white;
        font-size: 16px;
    }
    .persona-card p {
        color: #ecf0f1;
        font-size: 12px;
        line-height: 1.3;
        margin-bottom: 12px;
        flex-grow: 1;
    }
    .persona-card a {
        display: inline-block;
        padding: 6px 12px;
        color: white;
        font-weight: bold;
        text-decoration: none;
        border-radius: 50px;
        transition: background-color 0.3s ease;
        background-color: #4F4F4F;
        font-size: 12px;
        margin-top: auto;
    }
    .persona-card a:hover {
        background-color: #5F5F5F;
    }
    </style>
    <div class="persona-container">
    '''

    for persona in client_personas_data['personas']:
        img = load_image(persona['image'])
        if img:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            persona_html += f"""
            <div class="persona-card">
                <div class="image-container">
                    <img src="data:image/png;base64,{img_b64}" alt="{persona['name']}">
                </div>
                <h3>{persona['name']}</h3>
                <p>{persona['description']}</p>
                <a href="{persona['button_link']}" target="_blank">{persona['button_text']}</a>
            </div>
            """

    persona_html += '</div>'
    components.html(persona_html, height=total_height)

# Create a sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="",  # required
        options=["Home", "Questionnaire", "Client Personas", "Contact"],  # added Client Personas
        icons=["house", "clipboard-check", "people", "envelope"],  # added icon for Client Personas
        menu_icon="cast",  # optional
        default_index=0,  # optional
    )

# Update session state based on sidebar selection
if selected != st.session_state.page:
    st.session_state.page = selected

# Logic to display the selected page
if st.session_state.page == "Home":
    home()
elif st.session_state.page == "Questionnaire":
    Questionnaire()
elif st.session_state.page == "Client Personas":
    client_personas()
elif st.session_state.page == "Contact":
    contact()

# connection close.
conn.close()

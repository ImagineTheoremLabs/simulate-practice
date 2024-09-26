# scenario_challenge.py

import streamlit as st
import sqlite3
import json
import uuid
import re
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

# Load environment variables from .env file (if needed for other purposes)
load_dotenv()

# **1. API Key Configuration**
# Keep the API key as provided
GOOGLE_API_KEY = "AIzaSyCQMi_h02TMadAhW8ubeCI419vTv3UrnLE"

if not GOOGLE_API_KEY:
    st.error("Google API key not found. Please make sure it's set in the script.")
    st.stop()

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)


# **2. Database Connection and Setup**
def get_db_connection():
    conn = sqlite3.connect('responses.db')
    c = conn.cursor()
    # Create scenarios table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    conversation_history TEXT,
                    feedback TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()

    # Attempt to add 'conversation_history' column
    try:
        c.execute('ALTER TABLE scenarios ADD COLUMN conversation_history TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Attempt to add 'feedback' column
    try:
        c.execute('ALTER TABLE scenarios ADD COLUMN feedback TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    return conn


# **3. Helper Functions**
# Function to load CSS
def load_local_css(file_path):
    try:
        with open(file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file {file_path} not found.")
        return None


# Function to clean response text
def clean_response(text):
    # Remove asterisks and other formatting characters
    text = re.sub(r'[*_~`]', '', text)

    # Replace various types of dashes with regular hyphens
    text = re.sub(r'[–—−]', '-', text)

    # Add spaces after punctuation if missing
    text = re.sub(r'([.,!?;:])(?=\S)', r'\1 ', text)

    # Add spaces between words if missing (camel case split)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Add spaces between numbers and words if missing
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    # Fix spacing around apostrophes
    text = re.sub(r'\s\'', "'", text)
    text = re.sub(r'\'\s', "' ", text)

    # Remove repeated phrases (case insensitive)
    words = text.split()
    cleaned_words = []
    for i, word in enumerate(words):
        if i == 0 or word.lower() != words[i - 1].lower():
            cleaned_words.append(word)

    # Rejoin the words
    cleaned_text = ' '.join(cleaned_words)

    return cleaned_text.strip()


# Function to strip markdown
def strip_markdown(text):
    """
    Remove markdown formatting from text.
    """
    # Remove markdown headers
    text = re.sub(r'#+\s+', '', text)
    # Remove bold and italics
    text = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', text)
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text


# **4. Sample Scenarios**
SAMPLE_SCENARIOS = [
    {
        "title": "High-Risk Investor with Impending Life Changes",
        "description": "You are advising a 40-year-old client with a high-risk tolerance who wants to maximize retirement savings within a short period. However, they've just informed you that they're planning to start a family in the next year and may need to reduce work hours. They also have significant student loan debt and are considering purchasing a larger home. How do you balance their aggressive investment strategy with these upcoming life changes and financial obligations?"
    },
    {
        "title": "Near-Retiree with Limited Savings and Unexpected Inheritance",
        "description": "You are advising a 60-year-old client nearing retirement with limited savings. They've just inherited a significant sum from a distant relative, but the inheritance is mostly in the form of real estate and a small family business. The client is concerned about meeting their retirement income needs and is unsure how to manage or liquidate the inherited assets. They also have an adult child with special needs who requires ongoing financial support. How do you help them navigate this complex financial situation to ensure a stable retirement?"
    },
    {
        "title": "Tech Professional Interested in Sustainable Investing and Cryptocurrency",
        "description": "You are advising a 35-year-old tech professional who wants to invest in sustainable and socially responsible funds as part of their retirement portfolio. They're also very interested in cryptocurrency investments and have already allocated a significant portion of their savings to various digital assets. The client has stock options from their employer that are about to vest and is considering early retirement to pursue a passion project. How do you help them balance their interest in ethical investing with their high-risk crypto holdings and guide them on managing their soon-to-vest stock options?"
    },
    {
        "title": "Small Business Owner Nearing Retirement with Succession Planning Challenges",
        "description": "You are advising a 58-year-old small business owner who wants to retire in the next 5-7 years. Their retirement savings are mostly tied up in their business, which has been underperforming in recent years due to increased competition. They have two children: one who works in the business and is interested in taking over, and another who doesn't but expects an equal inheritance. The client also has unresolved tax issues from previous years and is considering selling the business to fund their retirement. How do you help them navigate the complexities of business succession, family dynamics, tax implications, and retirement planning?"
    }
]


# **5. Main Scenario Challenge Function**
def scenario_challenge():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths for CSS
    css_path = os.path.join(current_dir, "styles.css")
    load_local_css(css_path)

    conn = get_db_connection()
    c = conn.cursor()

    # Initialize session state for scenarios if not present
    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = None

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""

    st.title("Financial Scenario Challenge")
    st.markdown("---")

    # **1. Display Available Scenarios**
    st.subheader("Available Scenarios")
    num_columns = 2  # Number of columns per row
    for i in range(0, len(SAMPLE_SCENARIOS), num_columns):
        cols = st.columns(num_columns)
        for j in range(num_columns):
            if i + j < len(SAMPLE_SCENARIOS):
                scenario = SAMPLE_SCENARIOS[i + j]
                with cols[j]:
                    st.markdown(f'<div class="scenario-card">', unsafe_allow_html=True)

                    # **Removed Image Loading Here**
                    # If you decide to add images later, you can uncomment and adjust the code below:
                    # image_path = os.path.join(current_dir, "img", f"scenario_{i + j}.png")  # Example image path
                    # img = load_image(image_path)
                    # if img:
                    #     st.image(img, use_column_width=True)

                    st.markdown(f'<div class="scenario-title">{scenario["title"]}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="scenario-description">{scenario["description"]}</div>',
                                unsafe_allow_html=True)

                    # **2. Start Challenge Button Without `css_class`**
                    if st.button("Start Challenge", key=f"start_{i + j}"):
                        st.session_state.selected_scenario = scenario
                        st.session_state.conversation_history = []
                        st.session_state.feedback = ""
                        st.rerun()

                    st.markdown('</div>', unsafe_allow_html=True)

    # **2. Display Selected Scenario and Conversation**
    if st.session_state.selected_scenario:
        st.markdown("---")
        st.subheader(f"**Scenario:** {st.session_state.selected_scenario['title']}")
        st.markdown(f"*{st.session_state.selected_scenario['description']}*")

        st.markdown("### **Conversation:**")
        conversation_container = st.container()

        # Display conversation history
        with conversation_container:
            for message in st.session_state.conversation_history:
                if message["role"] == "advisor":
                    st.markdown(f"**Financial Advisor:** {message['content']}")
                elif message["role"] == "client":
                    st.markdown(f"**Client:** {message['content']}")

        # **3. Input for Advisor's Message**
        advisor_input = st.text_input("Your Message:", key="advisor_input")

        # **4. Button Group for Send and End Challenge**
        st.markdown('<div class="button-group">', unsafe_allow_html=True)
        send, end = st.columns(2)
        with send:
            if st.button("📨 Send", key="send_btn"):
                if advisor_input.strip() == "":
                    st.warning("Please enter a message before sending.")
                else:
                    # Append advisor's message to the conversation history
                    st.session_state.conversation_history.append({"role": "advisor", "content": advisor_input})

                    # Generate client's response using Gemini API
                    client_response = generate_client_response(
                        st.session_state.conversation_history,
                        st.session_state.selected_scenario
                    )

                    # Append client's response to the conversation history
                    st.session_state.conversation_history.append({"role": "client", "content": client_response})

                    st.rerun()
        with end:
            if st.button("🛑 End Challenge", key="end_challenge_btn"):
                # Generate feedback based on the conversation
                with st.spinner("Generating feedback..."):
                    feedback = generate_feedback(st.session_state.conversation_history)
                    st.session_state.feedback = feedback

                # Save the scenario, conversation, and feedback to the database
                scenario_id = str(uuid.uuid4())
                conversation_json = json.dumps(st.session_state.conversation_history)
                c.execute("""
                    INSERT INTO scenarios (id, title, description, conversation_history, feedback)
                    VALUES (?, ?, ?, ?, ?)
                """, (scenario_id, st.session_state.selected_scenario['title'],
                      st.session_state.selected_scenario['description'], conversation_json, feedback))
                conn.commit()

                st.success("Challenge ended. Feedback generated.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # **5. Display Feedback if Available**
        if st.session_state.feedback:
            st.markdown("---")
            st.markdown("### **Feedback:**")
            st.markdown(f'<div class="feedback-container">{st.session_state.feedback}</div>', unsafe_allow_html=True)

            # Option to reset the challenge
            if st.button("🔄 Start New Challenge", key="new_challenge_btn"):
                st.session_state.selected_scenario = None
                st.session_state.conversation_history = []
                st.session_state.feedback = ""
                st.rerun()

        # Option to reset the challenge at any point
        if st.button("🔄 Reset Challenge", key="reset_challenge_btn"):
            st.session_state.selected_scenario = None
            st.session_state.conversation_history = []
            st.session_state.feedback = ""
            st.rerun()

    # **3. Display Past Challenges**
    st.markdown("---")
    st.subheader("Your Past Challenges")
    c.execute("SELECT title, conversation_history, feedback, timestamp FROM scenarios ORDER BY timestamp DESC")
    past_challenges = c.fetchall()

    if past_challenges:
        for challenge in past_challenges:
            title, conversation_json, feedback, timestamp = challenge
            if conversation_json:
                try:
                    conversation = json.loads(conversation_json)
                except json.JSONDecodeError:
                    conversation = []
            else:
                conversation = []

            with st.expander(f"{title} - {timestamp}"):
                st.markdown("**Conversation:**")
                for message in conversation:
                    if message["role"] == "advisor":
                        st.markdown(f"**Financial Advisor:** {message['content']}")
                    elif message["role"] == "client":
                        st.markdown(f"**Client:** {message['content']}")
                st.markdown("**Feedback:**")
                st.markdown(f'<div class="feedback-container">{feedback}</div>', unsafe_allow_html=True)
    else:
        st.info("You haven't completed any challenges yet.")

    # **4. Manage Past Challenges**
    st.markdown("---")
    st.subheader("Manage Past Challenges")

    with st.form("clear_past_form"):
        st.warning("⚠️ **This action will delete all past challenges. This cannot be undone.**")
        confirm = st.checkbox("Are you sure you want to delete all past challenges?")
        submit = st.form_submit_button("Clear All Past Challenges")

        if submit:
            if confirm:
                try:
                    c.execute("DELETE FROM scenarios")
                    conn.commit()
                    st.success("✅ All past challenges have been cleared.")
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred while deleting challenges: {e}")
            else:
                st.warning("🛑 Deletion canceled. No challenges were deleted.")

    # **5. Close the Database Connection**
    conn.close()


# **6. Functions to Generate Responses and Feedback**
def generate_client_response(conversation_history, scenario):
    """
    Generate a response from the client using the Gemini API based on the conversation history and scenario.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare the conversation history
    chat_history = ""
    for message in conversation_history:
        role = "Financial Advisor" if message["role"] == "advisor" else "Client"
        chat_history += f"{role}: {message['content']}\n"

    # Construct the prompt
    prompt = f"""
You are roleplaying as a client in the following scenario:

Scenario: {scenario['title']}
Description: {scenario['description']}

Conversation so far:
{chat_history}

Financial Advisor: {conversation_history[-1]['content']}

Respond as the client, maintaining your persona and scenario context.
"""

    # Generate the response
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        if response.parts:
            raw_text = response.parts[0].text
            # Pre-process the text
            pre_processed_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_text)
            pre_processed_text = re.sub(r'([.,!?])(\S)', r'\1 \2', pre_processed_text)
            cleaned_text = clean_response(pre_processed_text)
            stripped_text = strip_markdown(cleaned_text)
            return stripped_text
        else:
            return "I'm sorry, I couldn't generate a response at this time."
    except Exception as e:
        return "I'm experiencing some issues and can't respond right now."


def generate_feedback(conversation_history):
    """
    Generate feedback based on the conversation history using the Gemini API.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare the conversation history
    chat_history = ""
    for message in conversation_history:
        role = "Financial Advisor" if message["role"] == "advisor" else "Client"
        chat_history += f"{role}: {message['content']}\n"

    # Construct the revised prompt for feedback
    prompt = f"""
You are an experienced financial advisor mentor. Review the following conversation between a financial advisor and a client, and provide constructive feedback to the advisor on their performance.

Conversation:
{chat_history}

Provide your feedback in a clear and organized manner with the following sections:

1. **Overall Assessment**
   - Brief overall assessment points.

2. **Strengths**
   - Strength 1
   - Strength 2
   - Strength 3

3. **Areas for Improvement**
   - Area 1: Brief explanation.
   - Area 2: Brief explanation.
   - Area 3: Brief explanation.

4. **Recommendations**
   - Recommendation 1: Brief explanation.
   - Recommendation 2: Brief explanation.
   - Recommendation 3: Brief explanation.

5. **Performance Ratings (out of 10)**
   - Communication: [Rating]
   - Technical Knowledge: [Rating]
   - Client Rapport: [Rating]
   - Overall Performance: [Rating]

6. **Conclusion**
   - Final thoughts and summary.
"""

    # Generate the feedback
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        if response.parts:
            raw_text = response.parts[0].text
            cleaned_feedback = clean_response(raw_text)
            stripped_feedback = strip_markdown(cleaned_feedback)
            return stripped_feedback
        else:
            return "I'm unable to provide feedback at this time."
    except Exception as e:
        return "I'm experiencing some issues and can't generate feedback right now."


# **7. Run the Streamlit App**
if __name__ == "__main__":
    scenario_challenge()

import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re
import uuid

# Assuming you have set up your Google API key
GOOGLE_API_KEY = "AIzaSyCQMi_h02TMadAhW8ubeCI419vTv3UrnLE"
genai.configure(api_key=GOOGLE_API_KEY)

# Custom CSS for improved aesthetics
st.markdown("""
<style>
    body {
        color: #e0e0e0;
        background-color: #121212;
    }
    .main {
        background-color: #1e1e1e;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stTextInput > div > div > input,
    .stSelectbox > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #2b2b2b;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 5px;
    }
    .stButton > button {
        background-color: #3d3d3d;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #4a4a4a;
        box-shadow: 0 2px 5px rgba(255, 255, 255, 0.1);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
        max-width: 100%;  /* Change this from 80% to 100% */
        width: 100%;      /* Add this line */
    }
    .chat-message.user {
        background-color: #2b313e;
        color: #ffffff;
        align-self: stretch;  /* Change this from flex-end to stretch */
        border-bottom-right-radius: 0;
    }
    .chat-message.bot {
        background-color: #3a3a3a;
        color: #ffffff;
        align-self: stretch;  /* Change this from flex-start to stretch */
        border-bottom-left-radius: 0;
    }
    .chat-message .message-content {
        display: flex;
        margin-bottom: 0.5rem;
    }
    .chat-message .message {
        width: 100%;
    }

    /* Add this new style */
    .stApp > header {
        background-color: transparent;
    }

    /* Optionally, adjust the main content area */
    .main .block-container {
        max-width: 100%;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    .persona-card {
        background-color: #1a1a1a;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border: 1px solid #333;
    }
    .persona-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(255, 255, 255, 0.1);
    }
    .persona-card h3 {
        color: #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #2b2b2b;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #3a3a3a;
        color: #ffffff;
        border-radius: 5px 5px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a4a4a;
    }
    .stMarkdown a {
        color: #a0a0a0;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #1e1e1e;
    }
    .stSidebar [data-testid="stSidebarNav"] {
        background-color: #2b2b2b;
        padding-top: 1rem;
    }
    .stSidebar [data-testid="stSidebarNav"] ul {
        padding-left: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for personas
if 'personas' not in st.session_state:
    st.session_state.personas = {}

def add_persona(name, description, profile):
    """Add a new persona to the session state."""
    st.session_state.personas[name] = {
        "name": name,
        "description": description,
        "profile": profile,
        "image": "img/default_persona_image.webp",  # Use a default image
        "additional_info": f"**Custom Persona:** {description}"
    }

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
        if i == 0 or word.lower() != words[i-1].lower():
            cleaned_words.append(word)
    
    # Rejoin the words
    cleaned_text = ' '.join(cleaned_words)
    
    return cleaned_text.strip()

def get_client_response(conversation_history, user_input, persona):
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Prepare the conversation history
    chat_history = ""
    for message in conversation_history[-5:]:  # Only use the last 5 messages for context
        role = "Financial Advisor" if message["role"] == "user" else "Client"
        chat_history += f"{role}: {message['content']}\n"

    # Construct the prompt
    prompt = f"""
You are roleplaying as {persona['name']}. Here is your full persona and background:

{persona['profile']}

Recent conversation:
{chat_history}

Financial Advisor: {user_input}

Respond as {persona['name']}, keeping these guidelines in mind:
1. Stay true to your persona, financial situation, goals, and concerns.
2. Be direct and honest about your financial information when asked specific questions.
3. Maintain a natural, conversational tone while showing your financial literacy level.
4. Express your specific concerns and goals when relevant.
5. Show your level of financial knowledge, but be open to professional advice.
6. If the question isn't about a specific financial detail, focus on your goals, concerns, or approach to retirement planning.
7. Feel free to ask follow-up questions to gain more insights from the advisor.
8. Do not repeat the financial advisor's question in your response.

{persona['name']}:
"""

    # Generate the response
    response = model.generate_content(
        prompt,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
    )

    # Extract and clean the text from the response
    if response.parts:
        raw_text = response.parts[0].text
        # Pre-process the text
        pre_processed_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_text)
        pre_processed_text = re.sub(r'([.,!?])(\S)', r'\1 \2', pre_processed_text)
        cleaned_text = clean_response(pre_processed_text)
        return cleaned_text
    else:
        return "I'm sorry, I couldn't generate a response at this time."

def create_persona_form():
    st.header("Create New Persona")
    
    use_ai_background = st.checkbox("Generate AI Background", value=True, 
                                    help="Use AI to generate a detailed background story")
    
    with st.form("new_persona_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", help="Enter the persona's full name")
            age = st.number_input("Age", min_value=18, max_value=100, value=30, help="Enter the persona's age")
            occupation = st.text_input("Occupation", help="Enter the persona's current job or profession")
        with col2:
            marital_status = st.selectbox("Marital Status", 
                                          ["Single", "Married", "Divorced", "Widowed"],
                                          help="Select the persona's marital status")
            dependents = st.number_input("Number of Dependents", min_value=0, max_value=10, value=0,
                                         help="Enter the number of dependents (e.g., children)")
            location = st.text_input("Location", help="Enter the city and state where the persona lives")
        
        st.subheader("Financial Information")
        col3, col4 = st.columns(2)
        with col3:
            annual_income = st.number_input("Annual Income ($)", min_value=0, value=50000, step=1000,
                                            help="Enter the persona's annual income")
            savings = st.number_input("Current Savings ($)", min_value=0, value=10000, step=1000,
                                      help="Enter the persona's current savings amount")
        with col4:
            debt = st.number_input("Total Debt ($)", min_value=0, value=0, step=1000,
                                   help="Enter the persona's total debt")
            risk_tolerance = st.select_slider("Risk Tolerance", 
                                              options=["Very Low", "Low", "Medium", "High", "Very High"],
                                              value="Medium",
                                              help="Select the persona's risk tolerance for investments")
        
        st.subheader("Investment Portfolio")
        col5, col6 = st.columns(2)
        with col5:
            stocks_percentage = st.slider("Stocks (%)", 0, 100, 30, help="Percentage of portfolio in stocks")
            bonds_percentage = st.slider("Bonds (%)", 0, 100, 30, help="Percentage of portfolio in bonds")
        with col6:
            cash_percentage = st.slider("Cash (%)", 0, 100, 20, help="Percentage of portfolio in cash")
            other_percentage = st.slider("Other Investments (%)", 0, 100, 20, help="Percentage in other investments")

        st.subheader("Retirement Savings Plans")
        col7, col8 = st.columns(2)
        with col7:
            has_401k = st.checkbox("Has 401(k)")
            if has_401k:
                _401k_balance = st.number_input("401(k) Balance ($)", min_value=0, value=0, step=1000)
                _401k_contribution = st.number_input("Annual 401(k) Contribution ($)", min_value=0, value=0, step=500)
        with col8:
            has_ira = st.checkbox("Has IRA")
            if has_ira:
                ira_type = st.selectbox("IRA Type", ["Traditional", "Roth"])
                ira_balance = st.number_input("IRA Balance ($)", min_value=0, value=0, step=1000)
                ira_contribution = st.number_input("Annual IRA Contribution ($)", min_value=0, value=0, step=500)

        st.subheader("Financial Products of Interest")
        financial_products = st.multiselect(
            "Select financial products of interest",
            ["Mutual Funds", "ETFs", "Annuities", "Life Insurance", "Real Estate Investment Trusts (REITs)", "Certificates of Deposit (CDs)"]
        )

        st.subheader("Retirement Goals")
        retirement_age = st.slider("Desired Retirement Age", min_value=50, max_value=75, value=65,
                                   help="Select the age at which the persona wants to retire")
        retirement_lifestyle = st.text_area("Desired Retirement Lifestyle", 
                                            help="Describe the persona's ideal retirement lifestyle")
        
        st.subheader("Background and Personality")
        financial_knowledge = st.select_slider("Financial Knowledge", 
                                               options=["Novice", "Basic", "Intermediate", "Advanced", "Expert"],
                                               value="Basic",
                                               help="Select the persona's level of financial knowledge")
        personality = st.text_area("Personality Traits", 
                                   help="Describe the persona's key personality traits")
        concerns = st.text_area("Financial Concerns", 
                                help="List any specific financial concerns or worries the persona has")
        
        if not use_ai_background:
            profile = st.text_area("Additional Background", height=150,
                                   help="Provide any additional background information or context for this persona")
        
        submitted = st.form_submit_button("Create Persona")
        
        if submitted:
            if name and occupation and location and retirement_lifestyle and personality and concerns:
                # Construct initial persona info
                persona_info = f"""
                Name: {name}
                Age: {age}
                Occupation: {occupation}
                Marital Status: {marital_status}
                Dependents: {dependents}
                Location: {location}
                Annual Income: ${annual_income:,}
                Current Savings: ${savings:,}
                Total Debt: ${debt:,}
                Risk Tolerance: {risk_tolerance}
                Investment Portfolio:
                - Stocks: {stocks_percentage}%
                - Bonds: {bonds_percentage}%
                - Cash: {cash_percentage}%
                - Other Investments: {other_percentage}%
                Retirement Savings Plans:
                - 401(k): {"Yes" if has_401k else "No"}
                {f"  - Balance: ${_401k_balance:,}" if has_401k else ""}
                {f"  - Annual Contribution: ${_401k_contribution:,}" if has_401k else ""}
                - IRA: {"Yes" if has_ira else "No"}
                {f"  - Type: {ira_type}" if has_ira else ""}
                {f"  - Balance: ${ira_balance:,}" if has_ira else ""}
                {f"  - Annual Contribution: ${ira_contribution:,}" if has_ira else ""}
                Financial Products of Interest: {", ".join(financial_products)}
                Desired Retirement Age: {retirement_age}
                Retirement Lifestyle: {retirement_lifestyle}
                Financial Knowledge: {financial_knowledge}
                Personality: {personality}
                Financial Concerns: {concerns}
                """
                
                # Generate AI background or use provided background
                if use_ai_background:
                    with st.spinner("Generating detailed background..."):
                        ai_background = generate_ai_background(persona_info)
                    full_profile = f"{persona_info}\n\nAI-Generated Background:\n{ai_background}"
                else:
                    full_profile = f"{persona_info}\n\nAdditional Background:\n{profile}"
                
                add_persona(name, f"{age}-year-old {occupation} from {location}", full_profile)
                st.success(f"Persona '{name}' added successfully!")
            else:
                st.error("Please fill in all required fields.")
                
                
def generate_ai_background(persona_info):
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Based on the following information about a fictional person, generate a detailed and realistic background story. Include details about their upbringing, education, career progression, major life events, and how these factors have shaped their current financial situation and retirement goals. Make the story engaging and consistent with the provided information.

    Information:
    {persona_info}

    Generate a background story of about 250-300 words.
    """

    response = model.generate_content(prompt)
    if response.parts:
        raw_text = response.parts[0].text
        # Pre-process the text
        pre_processed_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_text)
        pre_processed_text = re.sub(r'([.,!?])(\S)', r'\1 \2', pre_processed_text)
        cleaned_text = clean_response(pre_processed_text)
        return cleaned_text
    else:
        return "I'm sorry, I couldn't generate a response at this time."

def display_personas():
    st.header("Existing Personas")
    if not st.session_state.personas:
        st.info("No personas created yet. Create one to get started!")
    else:
        # CSS for the persona cards (unchanged)
        st.markdown("""
        <style>
        .persona-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            padding: 1rem;
        }
        .persona-card {
            background: linear-gradient(145deg, #2a2a2a, #333333);
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .persona-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
        }
        .persona-name {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .persona-description {
            color: #e0e0e0;
            font-size: 1.1rem;
            margin-bottom: 1.25rem;
            line-height: 1.4;
        }
        .persona-details {
            color: #b0b0b0;
            font-size: 0.95rem;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            padding: 1rem;
        }
        .persona-details p {
            margin: 0.5rem 0;
            display: flex;
            justify-content: space-between;
        }
        .persona-details strong {
            color: #d0d0d0;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create a grid container for the persona cards
        st.markdown('<div class="persona-grid">', unsafe_allow_html=True)

        for name, persona in st.session_state.personas.items():
            # Extract additional details from the persona profile
            def extract_detail(key):
                for line in persona['profile'].split('\n'):
                    if line.strip().startswith(key):
                        return line.split(':', 1)[1].strip()
                return 'N/A'

            age = extract_detail('Age')
            occupation = extract_detail('Occupation')
            location = extract_detail('Location')
            income = extract_detail('Annual Income')
            retirement_age = extract_detail('Desired Retirement Age')

            st.markdown(f"""
            <div class="persona-card">
                <h3 class="persona-name">{name}</h3>
                <p class="persona-description">{persona['description']}</p>
                <div class="persona-details">
                    <p><strong>Age:</strong> <span>{age}</span></p>
                    <p><strong>Occupation:</strong> <span>{occupation}</span></p>
                    <p><strong>Location:</strong> <span>{location}</span></p>
                    <p><strong>Annual Income:</strong> <span>{income}</span></p>
                    <p><strong>Desired Retirement Age:</strong> <span>{retirement_age}</span></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Close the grid container
        st.markdown('</div>', unsafe_allow_html=True)

        # Add a button to view full profiles
        if 'show_full_profiles' not in st.session_state:
            st.session_state.show_full_profiles = False

        if st.button("Toggle Full Profiles"):
            st.session_state.show_full_profiles = not st.session_state.show_full_profiles

        # Display full profiles if toggled
        if st.session_state.show_full_profiles:
            st.subheader("Full Profiles")
            for name, persona in st.session_state.personas.items():
                with st.expander(f"Full Profile: {name}"):
                    st.text_area("", value=persona['profile'], height=300, key=f"profile_{name}")

def client_chat_interface():
    st.title("Retirement Planning Simulation")

    if not st.session_state.personas:
        st.warning("No personas created yet. Please create a persona first.")
        return

    # Persona selection
    persona_names = list(st.session_state.personas.keys())
    selected_persona = st.selectbox("Select a client persona:", persona_names)

    if selected_persona:
        persona = st.session_state.personas[selected_persona]
        st.subheader(f"Chatting with: {selected_persona}")
        st.write(persona['description'])

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "chat_id" not in st.session_state:
            st.session_state.chat_id = str(uuid.uuid4())

        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.container():
                    st.markdown(f"""
                    <div class="chat-message user">
                        <div class="message-content">
                            <div class="message">
                                {message["content"]}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown(f"""
                    <div class="chat-message bot">
                        <div class="message-content">
                            <div class="message">
                                {message["content"]}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # User input form
        with st.form(key="user_input_form"):
            user_input = st.text_input(f"What would you like to ask {selected_persona}?", key="user_input")
            col1, col2 = st.columns([4, 1])
            with col1:
                submit_button = st.form_submit_button(label="Send")
            with col2:
                end_chat_button = st.form_submit_button(label="End Chat")

        if submit_button and user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Get and display client response
            with st.spinner(f"{selected_persona} is thinking..."):
                client_response = get_client_response(st.session_state.messages, user_input, {"name": selected_persona, "profile": persona['profile']})

            # Add client response to chat history
            st.session_state.messages.append({"role": "assistant", "content": client_response})

            # Rerun the app to update the chat display
            st.rerun()

        if end_chat_button:
            # Clear the chat history
            st.session_state.messages = []
            st.session_state.chat_id = str(uuid.uuid4())
            st.success("Chat ended. You can start a new conversation.")
            st.rerun()

# Streamlit app
def main():
    
    
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to", ["Create Persona", "Chat", "View Personas"])

    if page == "Chat":
        client_chat_interface()
    elif page == "Create Persona":
        create_persona_form()
    elif page == "View Personas":
        display_personas()

# Run the Streamlit app
if __name__ == "__main__":
    main()
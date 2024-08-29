import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import json
import base64
from PIL import Image
import io
import streamlit.components.v1 as components
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re
import uuid
import base64
from PIL import Image
import io
import re
import os
from dotenv import load_dotenv

st.set_page_config(layout="wide")

def load_image(image_path):
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        st.error(f"Image file {image_path} not found.")
        return None

# Load environment variables from .env file
load_dotenv()

# Fetch the API key from the environment
GOOGLE_API_KEY = "AIzaSyCQMi_h02TMadAhW8ubeCI419vTv3UrnLE"
# GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

if not GOOGLE_API_KEY:
    st.error("Google API key not found. Please make sure it's set in the .env file.")
    st.stop()  # This will halt the execution of the Streamlit app

# If we get here, we have an API key
import google.generativeai as genai


genai.configure(api_key=GOOGLE_API_KEY)


# Gemini API setup
genai.configure(api_key=GOOGLE_API_KEY)


# Load content from JSON files
with open('data/home_content.json', 'r') as f:
    home_content = json.load(f)

# Database setup
conn = sqlite3.connect('responses.db')
c = conn.cursor()

# Check if the table exists
c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='responses' ''')

# If the table doesn't exist, create it with the new schema
if c.fetchone()[0] == 0:
    c.execute('''CREATE TABLE responses
                 (name TEXT, email TEXT, experience TEXT, advise_frequency TEXT, 
                  client_types TEXT, knowledge_ratings TEXT, challenges TEXT, goals TEXT)''')
else:
    # If the table exists, alter it to add the new columns
    try:
        c.execute('ALTER TABLE responses ADD COLUMN name TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN email TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN experience TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN advise_frequency TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN client_types TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN knowledge_ratings TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN challenges TEXT')
        c.execute('ALTER TABLE responses ADD COLUMN goals TEXT')
    except sqlite3.OperationalError:
        # If columns already exist, this error will be raised. We can ignore it.
        pass

conn.commit()

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Load image function
def load_image(image_path):
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        st.error(f"Image file {image_path} not found.")
        return None

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
    
    if st.button("Go to Questionnaire"):
        st.session_state.page = "Questionnaire"
        st.experimental_rerun()

def questionnaire():
    st.title("Advisor Questionnaire")
    st.markdown("""
    <style>
    .big-font {
        font-size:20px !important;
        font-weight: bold;
    }
    .stRadio > label {
        font-weight: bold;
        color: #3366cc;
    }
    .stTextInput > label {
        font-weight: bold;
        color: #3366cc;
    }
    .submit-btn {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Hello Advisor, Please answer the following questions:</p>', unsafe_allow_html=True)

    # Personal Information
    st.subheader("Personal Information")
    name = st.text_input("1. Name:")
    email = st.text_input("2. Email:")
    experience = st.radio("3. Years of Experience in Financial Advisory:",
                          ("Less than 1 year", "1-3 years", "4-7 years", "8+ years"))

    # Client Engagement
    st.subheader("Client Engagement")
    advise_frequency = st.radio("1. How often do you advise clients on retirement planning?",
                                ("Frequently", "Occasionally", "Rarely", "Never"))
    client_types = st.multiselect("2. Which types of clients do you primarily work with? (Select all that apply)",
                                  ["High-income earners", "Business owners", "Middle-income earners",
                                   "Individuals nearing retirement", "Young professionals"])

    # Retirement Planning Knowledge
    st.subheader("Retirement Planning Knowledge")
    knowledge_areas = ["Retirement savings strategies", "Investment options for retirement",
                       "Social Security benefits", "Healthcare planning for retirement",
                       "Tax planning for retirement"]
    knowledge_ratings = {}
    st.write("1. How confident are you in your knowledge of the following areas? (Rate on a scale of 1-5, with 1 being 'Not Confident' and 5 being 'Very Confident')")
    for area in knowledge_areas:
        knowledge_ratings[area] = st.slider(area, 1, 5, 3)

    challenges = st.multiselect("2. What are the biggest challenges you face when advising clients on retirement planning? (Select up to three)",
                                ["Lack of client knowledge", "Market volatility", "Healthcare cost planning",
                                 "Tax implications", "Client engagement and follow-through", "Managing debt"],
                                max_selections=3)

    # Training Goals
    st.subheader("Training Goals")
    goals = st.multiselect("1. What are your primary goals for using the Retirement Readiness Simulator? (Select all that apply)",
                           ["Improve overall knowledge of retirement planning",
                            "Enhance client engagement techniques",
                            "Practice handling different client scenarios",
                            "Gain confidence in providing retirement advice",
                            "Learn advanced retirement strategies"])

    if st.button("Submit", key="submit_btn", help="Click to submit your responses"):
        if all([name, email, experience, advise_frequency, client_types, challenges, goals]):
            # Store the responses in the database
            responses = {
                "name": name,
                "email": email,
                "experience": experience,
                "advise_frequency": advise_frequency,
                "client_types": ", ".join(client_types),
                "knowledge_ratings": json.dumps(knowledge_ratings),
                "challenges": ", ".join(challenges),
                "goals": ", ".join(goals)
            }
            c.execute("""
                INSERT INTO responses 
                (name, email, experience, advise_frequency, client_types, knowledge_ratings, challenges, goals) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(responses.values()))
            conn.commit()
            st.success("Your responses have been submitted successfully!")
            
            # Add a small delay before changing the page
            time.sleep(2)
            st.session_state.page = "Client"
            st.experimental_rerun()
        else:
            st.warning("Please answer all questions before submitting.")


def client_personas():
    # Sarah's full persona
    sarah_persona = """
    You are Sarah Johnson, a 55-year-old Senior Executive at a Tech Company seeking retirement advice. Your details are:

    Financial Information:
    - Annual Income: $250,000
    - Retirement Savings: $1.5 million in 401(k), IRA, and other investments
    - Financial Literacy: High
    - Current Tax Bracket: 32%

    Investment Portfolio:
    - Stocks: $700,000 (diversified across tech, healthcare, and blue-chip companies)
    - Bonds: $300,000 (municipal bonds, treasury bonds)
    - Mutual Funds: $200,000 (index funds, sector-specific funds)
    - Real Estate Investments: $150,000 (rental property generating additional income)
    - Cash Reserves: $150,000 (emergency fund and short-term savings)

    Insurance:
    - Health Insurance: Comprehensive coverage through your employer
    - Life Insurance: $1 million term life policy
    - Long-Term Care Insurance: Policy in place
    - Disability Insurance: Policy through your employer

    Expenses:
    - Monthly Living Expenses: $8,000
    - Annual Travel Budget: $20,000
    - Healthcare Costs: $5,000 annually

    Goals and Concerns:
    - Retire at 60
    - Travel extensively in retirement
    - Maintain current lifestyle (requiring about $150,000 annually in retirement)
    - Concerned about market volatility and its impact on retirement savings
    - Worried about future healthcare costs
    - Interested in tax-efficient withdrawal strategies and Roth conversions
    - Want to leave a substantial inheritance for children and grandchildren

    Personal Traits:
    - Well-versed in financial planning
    - Actively manages retirement savings
    - Confident in financial knowledge but seeks professional advice for optimization
    - Regular reviewer of investment portfolio
    - Open to new strategies but cautious about potential risks
    - Values work-life balance and looking forward to an active retirement

    Approach to Financial Advice:
    - Seeks to optimize retirement strategy
    - Wants to ensure full preparation for potential risks
    - Interested in balancing growth with security in investments
    - Open to sophisticated financial products and strategies
    - Keen on understanding the reasoning behind financial recommendations
    """

    # John's full persona
    john_persona = """
        You are John Miller, a 50-year-old Business Owner seeking retirement advice. Your details are:

        Description:
        Name: John Miller
        Age: 50
        Occupation: Business Owner
        Annual Income: $300,000
        Retirement Savings: $800,000 in various accounts, but not actively managed
        Financial Literacy: Moderate
        Goals: Retire at 65, start a hobby business, spend more time with family
        Concerns: Lack of knowledge about retirement planning, unsure about investment strategies, unaware of potential healthcare costs
        Profile: John has accumulated substantial wealth but has not actively planned for retirement. He is focused on his business and personal life, leaving little time to manage or understand his retirement savings. John is aware that he needs to start planning but is unsure where to begin and what steps to take.
        Key Attributes:
        * Financially strong but lacks retirement planning knowledge
        * Passive in managing investments
        * Seeks basic guidance and education on retirement readiness
        * Concerned about potential gaps in his retirement plan
        Scenario Interaction: John engages with the advisor to get a comprehensive overview of retirement planning. He needs education on the importance of diversifying investments, understanding retirement accounts, and planning for future healthcare costs. The advisor provides step-by-step guidance and helps John create a detailed retirement plan.

        Investment Portfolio:
        * Stocks: $200,000 (mix of individual stocks and ETFs, primarily in large-cap companies)
        * Bonds: $150,000 (corporate bonds, bond funds)
        * Mutual Funds: $250,000 (target-date retirement funds, balanced funds)
        * Real Estate Investments: $100,000 (commercial property related to his business)
        * Cash Reserves: $100,000 (emergency fund and business operating expenses)

        Insurance:
        * Health Insurance: High-deductible health plan through his business
        * Life Insurance: $500,000 whole life policy
        * Disability Insurance: Policy providing income protection for personal and business expenses
        * Business Insurance: Comprehensive coverage for his business, including liability and property insurance

        Expenses:
        * Monthly Living Expenses: $10,000 (housing, utilities, groceries, transportation, entertainment)
        * Annual Vacation Budget: $15,000
        * Healthcare Costs: $3,000 annually (out-of-pocket expenses, medications)
        * Education Savings: $100,000 (contributions to children's education funds)

        Tax Considerations:
        * Current Tax Bracket: 35%
        * Business Tax Strategy: Utilizing tax deductions and credits to minimize taxable income

        Financial Goals:
        * Retirement Income: $120,000 annually to maintain current lifestyle
        * Hobby Business: Invest $50,000 to start a small, passion-driven business post-retirement
        * Family Time: Prioritizing spending time with family, potentially relocating to be closer to children and grandchildren
        """

        # Emily's full persona
    emily_persona = """
        You are Emily Davis, a 45-year-old Marketing Manager seeking retirement advice. Your details are:

        Name: Emily Davis
        Age: 45
        Occupation: Marketing Manager
        Annual Income: $90,000
        Retirement Savings: $50,000 in a 401(k)
        Financial Literacy: Low
        Goals: Retire at 65, downsize home, live comfortably
        Concerns: Insufficient savings, debt management, lack of investment knowledge
        Profile: Emily has not prioritized retirement savings and finds herself significantly behind in her retirement planning. She has some debt and limited knowledge of investment options. Emily is starting to realize the importance of planning for retirement but feels overwhelmed and unsure about how to catch up.

        Key Attributes:
        * Financially unprepared for retirement
        * Limited savings and investment knowledge
        * Concerned about debt and insufficient savings
        * Needs foundational advice and a catch-up strategy

        Scenario Interaction: Emily engages with the advisor seeking a realistic plan to become retirement ready. The advisor helps her understand the basics of retirement planning, prioritize debt reduction, and develop a savings plan. Emily is guided through setting up automatic contributions, exploring employer match options, and understanding the importance of starting early and staying consistent.

        Investment Portfolio:
        * 401(k): $50,000 (primarily in target-date retirement funds)
        * Emergency Savings: $5,000 (in a high-yield savings account)

        Debt:
        * Credit Card Debt: $10,000 (carrying a balance with high-interest rates)
        * Student Loans: $20,000 (monthly payments of $300)
        * Mortgage: $200,000 remaining balance (monthly payment of $1,200)

        Insurance:
        * Health Insurance: Through her employer with moderate coverage
        * Life Insurance: $250,000 term life policy
        * Disability Insurance: Policy through her employer providing partial income replacement

        Expenses:
        * Monthly Living Expenses: $3,500 (housing, utilities, groceries, transportation, entertainment)
        * Annual Vacation Budget: $2,000
        * Healthcare Costs: $1,000 annually (out-of-pocket expenses, medications)

        Tax Considerations:
        * Current Tax Bracket: 22%
        * Tax Strategy: Exploring ways to maximize tax-advantaged accounts

        Financial Goals:
        * Debt Reduction: Prioritize paying off credit card debt and student loans
        * Retirement Savings: Increase 401(k) contributions to at least 10% of her income
        * Home Downsize: Plan to sell current home and purchase a smaller, more affordable one upon retirement
        * Emergency Fund: Build up to 6 months' worth of living expenses
        """

        # Mentor Agent persona
    mentor_persona = """
    You are an experienced financial advisor mentor. Your role is to provide real-time advice to the financial advisor (the user) on how to conduct the assessment with the client and suggest improvements. You should:

    1. Observe the conversation between the financial advisor and the client.
    2. Provide constructive feedback on the advisor's approach.
    3. Suggest questions or topics that the advisor should explore further.
    4. Offer tips on how to better address the client's concerns and goals.
    5. Highlight any missed opportunities or areas where the advisor could dive deeper.
    6. Provide guidance on best practices in retirement planning and client communication.

    Your advice should be concise, actionable, and focused on improving the quality of the financial assessment and advice given to the client.
    """

    evaluator_persona = """
    You are an expert financial advisor evaluator. Your role is to review the entire conversation between the financial advisor and the client, and provide a comprehensive evaluation of the advisor's performance. You should:
    Give a line answer.
    """

    client_personas = [
        {
            "name": "Sarah Johnson",
            "description": "55-year-old Senior Executive at a Tech Company seeking retirement advice.",
            "image": "img/passport_like_photo_of_a_person_in_a_suit-2.jpeg",
            "profile": sarah_persona,
            "additional_info": """
            **Profile:** Sarah is well-versed in financial planning and has been actively managing her retirement savings for years. She has a clear understanding of her retirement goals and regularly reviews her investment portfolio. Sarah is confident but seeks professional advice to optimize her retirement strategy and ensure she's fully prepared for any potential risks.
            
            **Scenario Interaction:** Sarah engages with the advisor to review her current retirement plan, seeking advice on fine-tuning her investment strategy, minimizing tax liabilities, and planning for healthcare costs. She asks detailed questions and is interested in sophisticated financial products and strategies.
            """
        },
        {
            "name": "John Miller",
            "description": "50-year-old Business Owner seeking retirement advice.",
            "image": "img/passport_like_photo_of_a_person_in_a_suit-2.jpeg",
            "profile": john_persona,
            "additional_info": """
            **Profile:** John has accumulated substantial wealth but has not actively planned for retirement. He is focused on his business and personal life, leaving little time to manage or understand his retirement savings. John is aware that he needs to start planning but is unsure where to begin and what steps to take.
            
            **Scenario Interaction:** John engages with the advisor to get a comprehensive overview of retirement planning. He needs education on the importance of diversifying investments, understanding retirement accounts, and planning for future healthcare costs. The advisor provides step-by-step guidance and helps John create a detailed retirement plan.
            """
        },
        {
            "name": "Emily Davis",
            "description": "45-year-old Marketing Manager seeking retirement advice.",
            "image": "img/passport_like_photo_of_a_person_in_a_suit-2.jpeg",
            "profile": emily_persona,
            "additional_info": """
            **Profile:** Emily has not prioritized retirement savings and finds herself significantly behind in her retirement planning. She has some debt and limited knowledge of investment options. Emily is starting to realize the importance of planning for retirement but feels overwhelmed and unsure about how to catch up.
            
            **Scenario Interaction:** Emily engages with the advisor seeking a realistic plan to become retirement ready. The advisor helps her understand the basics of retirement planning, prioritize debt reduction, and develop a savings plan. Emily is guided through setting up automatic contributions, exploring employer match options, and understanding the importance of starting early and staying consistent.
            """
        }
    ]


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
    5. Show that you're knowledgeable about finances to the extent of your financial literacy, but open to professional advice.
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

    def get_mentor_advice(conversation_history):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the conversation history
        chat_history = ""
        for message in conversation_history[-10:]:  # Use the last 10 messages for context
            role = "Financial Advisor" if message["role"] == "user" else "Client"
            chat_history += f"{role}: {message['content']}\n"
        
        prompt = f"""
        {mentor_persona}

        Here's the recent conversation between the financial advisor and the client:

        {chat_history}

        Based on this conversation, provide 5 bullet points of actionable advice to the financial advisor on how to improve their assessment and better address the client's needs. Format your response as follows:

    • [Advice point 1]
    • [Advice point 2]
    • [Advice point 3]
    • [Advice point 4]
    • [Advice point 5]

        Mentor Agent:
        """
        
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
            return clean_response(response.parts[0].text)
        else:
            return "I don't have any specific advice at this moment. Continue the conversation with the client."



    def get_evaluator_feedback(conversation_history):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the entire conversation history
        chat_history = ""
        for message in conversation_history:
            role = "Financial Advisor" if message["role"] == "user" else "Client"
            chat_history += f"{role}: {message['content']}\n"
        
        prompt = f"""
        {evaluator_persona}

Here's the entire conversation between the financial advisor and the client:

{chat_history}

Based on this conversation, provide a comprehensive evaluation of the financial advisor's performance. Use the following format:

Overall Assessment:
- [Brief overall assessment point 1]
- [Brief overall assessment point 2]

Strengths:
- [Strength 1]
- [Strength 2]
- [Strength 3]

Areas for Improvement:
- [Area 1]: [Brief explanation]
- [Area 2]: [Brief explanation]
- [Area 3]: [Brief explanation]

Recommendations:
- [Recommendation 1]: [Brief explanation]
- [Recommendation 2]: [Brief explanation]
- [Recommendation 3]: [Brief explanation]

Performance Ratings (out of 10):
- Communication: [Rating]
- Technical Knowledge: [Rating]
- Client Rapport: [Rating]
- Overall Performance: [Rating]

Conclusion:
[Final thoughts and summary]


        Evaluator Agent:
        """
        
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
            return clean_response(response.parts[0].text)
        else:
            return "I'm unable to provide an evaluation at this time. Please review the conversation yourself."

    # Streamlit UI
    st.title("Retirement Planning Simulation for Financial Advisors")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "show_mentor" not in st.session_state:
        st.session_state.show_mentor = False

    if "chat_started" not in st.session_state:
        st.session_state.chat_started = False

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None

    if "current_persona" not in st.session_state:
        st.session_state.current_persona = None

    # Persona selection
    if not st.session_state.chat_started:
        st.write("Choose one of the following clients to begin your retirement planning simulation:")
        
        for i, persona in enumerate(client_personas):
            with st.container():
                st.subheader(f"{persona['name']} - {persona['description']}")
                col1, col2 = st.columns([1, 2])
                with col1:
                    img = load_image(persona['image'])
                    if img:
                        st.image(img, use_column_width=True)
                with col2:
                    st.markdown(persona['additional_info'])
                
                if st.button(f"Start Simulation with {persona['name']}", key=f"btn_{i}"):
                    st.session_state.chat_started = True
                    st.session_state.chat_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    st.session_state.current_persona = persona
                    st.experimental_rerun()
            
            # Add a divider between client profiles
            st.divider()

    if st.session_state.chat_started and st.session_state.current_persona:
        # Sidebar for controls
        with st.sidebar:
            st.subheader("Chat Controls")
            st.session_state.show_mentor = st.checkbox("Show Mentor Advice", value=st.session_state.show_mentor)
            
            if st.button("Reset Conversation", key="reset_btn"):
                st.session_state.messages = []
                st.session_state.chat_started = False
                st.session_state.current_persona = None
                st.experimental_rerun()
            
            if st.button("End Chat", key="end_btn"):
                st.session_state.chat_ended = True
                st.experimental_rerun()
        
        # Main chat interface
        st.subheader(f"Chatting with {st.session_state.current_persona['name']}")
        
        # Create a container for the chat messages
        chat_container = st.container()
        
        # Create a container for the input field
        input_container = st.container()
        
        # Display messages in the chat container
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input for new messages (placed at the bottom)
        with input_container:
            prompt = st.chat_input(f"What would you like to ask {st.session_state.current_persona['name']}?")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.markdown(f"**Financial Advisor:** {prompt}")

            with chat_container.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner(f"{st.session_state.current_persona['name']} is thinking..."):
                    full_response = get_client_response(st.session_state.messages, prompt, st.session_state.current_persona)
                    # Additional cleaning step
                    display_response = clean_response(full_response)
                message_placeholder.markdown(f"{display_response}")
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Mentor Agent
            # Mentor Agent
            # Mentor Agent
            # Mentor Agent
            if st.session_state.show_mentor:
                with chat_container.chat_message("mentor"):
                    mentor_placeholder = st.empty()
                    with st.spinner("Mentor is analyzing..."):
                        mentor_advice = get_mentor_advice(st.session_state.messages)
                    
                    # Display the header
                    st.markdown("**Mentor Agent:**")
                    
                    # Check if mentor_advice contains bullet points
                    if '•' in mentor_advice:
                        # Split the advice into bullet points
                        advice_points = mentor_advice.split('•')
                        
                        # Display each bullet point
                        for point in advice_points[1:]:  # Skip the first split as it's usually empty
                            if point.strip():  # Check if the point is not just whitespace
                                st.markdown(f"• {point.strip()}")
                    else:
                        # If there are no bullet points, display the advice as is
                        st.markdown(mentor_advice)

            # Remove this part as it's redundant and causes the error
            # Display the header
            # st.markdown("**Mentor Agent:**")

            # Display each bullet point
            # for point in advice_points[1:]:  # Skip the first split as it's usually empty
            #     st.markdown(f"• {point.strip()}")

            # Scroll to the bottom of the chat
            st.query_params["scroll_to_bottom"] = True

        # Display Evaluator feedback after ending the chat
        # Display Evaluator feedback after ending the chat
        # Display Evaluator feedback after ending the chat
        # Display Evaluator feedback after ending the chat
 

        # Display Evaluator feedback after ending the chat


        def clean_and_format_text(text):
            # Remove any single letters that are alone on a line
            text = re.sub(r'^[a-zA-Z]$', '', text, flags=re.MULTILINE)
            # Remove any remaining newlines
            text = re.sub(r'\n+', ' ', text)
            # Clean up extra spaces
            text = re.sub(r'\s+', ' ', text).strip()
            return text

        # Display Evaluator feedback after ending the chat
        if 'chat_ended' in st.session_state and st.session_state.chat_ended:
            st.subheader("Chat Ended - Evaluator Feedback")
            with st.spinner("Evaluator is reviewing the conversation..."):
                evaluator_feedback = get_evaluator_feedback(st.session_state.messages)
            
            # Clean and format the text
            evaluator_feedback = clean_and_format_text(evaluator_feedback)
            
            # Display the header
            st.markdown("### Evaluator Agent:")
            
            # Split the feedback into sections
            sections = re.split(r'(?=\b(?:Overall Assessment|Strengths|Areas for Improvement|Recommendations|Performance Ratings|Conclusion)\b)', evaluator_feedback)
            
            for section in sections:
                if section.strip():
                    # Split the section into title and content
                    parts = re.split(r':', section, 1)
                    if len(parts) > 1:
                        title, content = parts
                        st.markdown(f"#### {title.strip()}")
                        
                        # Split content into bullet points
                        points = re.split(r'•|-', content)
                        for point in points:
                            point = point.strip()
                            if point:
                                if 'out of 10' in point.lower():
                                    key, value = re.split(r':', point, 1)
                                    st.markdown(f"**{key.strip()}:** {value.strip()}")
                                else:
                                    st.markdown(f"• {point}")
                    else:
                        st.markdown(section)
                
                # Add a separator between sections
                st.markdown("---")
            
            if st.button("Start New Chat"):
                st.session_state.messages = []
                st.session_state.chat_started = False
                st.session_state.current_persona = None
                st.session_state.chat_ended = False
                st.experimental_rerun()

    else:
        st.write("Please select a client to start the conversation.")

# Sidebar
with st.sidebar:
    selected = option_menu(
        menu_title="Navigation",
        options=["Simulation"],
        icons=["play-circle"],
        menu_icon="cast",
        default_index=0,
    )

# Main app logic
if selected == "Simulation":
    if st.session_state.page == "Home":
        home()
    elif st.session_state.page == "Questionnaire":
        questionnaire()
    elif st.session_state.page == "Client":
        client_personas()

# Close the database connection
conn.close()

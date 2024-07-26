import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3


# Database setup
conn = sqlite3.connect('responses.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS responses
             (mcq1 TEXT, mcq2 TEXT, mcq3 TEXT, txt1 TEXT, txt2 TEXT)''')
conn.commit()


# Define a function for each page
def home():
    st.title("Retirement Readiness")
    st.write("Welcome to the home page!")



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

# Create a sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="",  # required
        options=["Home", "Questionnaire", "Contact"],  # required
        icons=["house", "clipboard-check", "envelope"],  # optional
        menu_icon="cast",  # optional
        default_index=0,  # optional
    )

# Logic to display the selected page
if selected == "Home":
    home()
elif selected == "Questionnaire":
    Questionnaire()
elif selected == "Contact":
    contact()

# connection close.
conn.close()
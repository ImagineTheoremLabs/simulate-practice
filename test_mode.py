import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re
import random
import json
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential

def configure_genai(api_key):
    genai.configure(api_key=api_key)

class TestModeManager:
    def __init__(self):
        self.load_test_history()
        self.initialize_test_state()
        self.simulations = self.get_simulations()

    def load_test_history(self):
        if 'test_history' not in st.session_state:
            try:
                with open('test_history.json', 'r') as f:
                    st.session_state.test_history = json.load(f)
            except FileNotFoundError:
                st.session_state.test_history = []

    def save_test_results(self, results):
        st.session_state.test_history.append(results)
        with open('test_history.json', 'w') as f:
            json.dump(st.session_state.test_history, f)

    def initialize_test_state(self):
        st.session_state.test_state = {
            "current_simulation": 0,
            "simulations_completed": 0,
            "scores": [],
            "chat_histories": [],
            "overall_score": None,
            "feedback": None,
            "strengths": [],
            "weaknesses": []
        }
        if 'messages' in st.session_state:
            del st.session_state.messages
                    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    def make_api_call(self, model, prompt):
        return model.generate_content(
            prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

    def get_simulations(self):
        return [
            {
                "title": "Retirement Planning for a Young Professional",
                "description": "Advise a 28-year-old software engineer on starting their retirement planning."
            },
            {
                "title": "Mid-Career Savings Boost",
                "description": "Help a 45-year-old teacher increase their retirement savings in the face of rising living costs."
            },
            {
                "title": "Pre-Retirement Portfolio Review",
                "description": "Review and adjust the portfolio of a 58-year-old executive planning to retire in 5 years."
            },
            {
                "title": "Retirement Income Strategy",
                "description": "Develop an income strategy for a newly retired couple worried about market volatility."
            },
            {
                "title": "Estate Planning and Inheritance",
                "description": "Advise a retiree on incorporating a recent inheritance into their estate and retirement plans."
            }
        ]

    def get_client_response(self, conversation_history, user_input, simulation):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        chat_history = "\n".join([f"{'Advisor' if msg['role'] == 'user' else 'Client'}: {msg['content']}" for msg in conversation_history[-5:]])
        
        prompt = f"""
        You are roleplaying as a client in the following simulation:

        Title: {simulation['title']}
        Description: {simulation['description']}

        Recent conversation:
        {chat_history}

        Financial Advisor: {user_input}

        Respond as the client, keeping these guidelines in mind:
        1. Stay in character and be consistent with the simulation scenario.
        2. Respond directly to the advisor's questions or statements.
        3. If asked for specific financial information, provide it without hesitation, inventing realistic details that fit the scenario.
        4. Don't ask for clarification unless the advisor's question is genuinely unclear or too broad.
        5. Show a level of financial knowledge appropriate to your character.
        6. Be open to advice but also critical and thoughtful about your financial decisions.

        Remember, you are a {simulation['description']}. Provide responses that reflect this character and their financial situation.

        Client:
        """
        
        response = self.make_api_call(model, prompt)
        
        return response.parts[0].text if response.parts else "I'm sorry, I couldn't generate a response at this time."

    def evaluate_simulation(self, conversation_history, simulation):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        chat_history = "\n".join([f"{'Advisor' if msg['role'] == 'user' else 'Client'}: {msg['content']}" for msg in conversation_history])
        
        prompt = f"""
        Evaluate the financial advisor's performance in the following simulation:

        Title: {simulation['title']}
        Description: {simulation['description']}

        Conversation:
        {chat_history}

        Please provide:
        1. A score out of 100 based on the advisor's performance.
        2. A brief explanation of the score (2-3 sentences).
        3. One key strength demonstrated by the advisor.
        4. One area for improvement.

        Format your response as follows:
        Score: [number]
        Explanation: [Your explanation here]
        Key Strength: [Strength]
        Area for Improvement: [Improvement]
        """
        
        response = self.make_api_call(model, prompt)
        return response.parts[0].text if response.parts else "Unable to generate evaluation at this time."

    def generate_overall_feedback(self, scores, evaluations):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Based on the following scores and evaluations from {len(scores)} simulations, provide an overall assessment of the financial advisor's performance:

        Scores: {', '.join(map(str, scores))}
        Average Score: {sum(scores) / len(scores):.2f}

        Individual Evaluations:
        {evaluations}

        Please provide:
        1. A summary of the advisor's overall performance (3-4 sentences).
        2. Three key strengths demonstrated across the simulations.
        3. Three main areas for improvement.
        4. Recommendations for further development (2-3 points).

        Format your response as follows:
        Overall Performance: [Your summary here]

        Key Strengths:
        1. [Strength 1]
        2. [Strength 2]
        3. [Strength 3]

        Areas for Improvement:
        1. [Area 1]
        2. [Area 2]
        3. [Area 3]

        Recommendations:
        - [Recommendation 1]
        - [Recommendation 2]
        - [Recommendation 3]
        """
        
        response = model.generate_content(prompt)
        return response.parts[0].text if response.parts else "Unable to generate overall feedback at this time."

    def run_test_mode(self):
        st.title("Test Mode: Self-Guided Simulations")

        # Initialize or reset test state if needed
        if 'test_mode_initialized' not in st.session_state:
            self.initialize_test_state()
            st.session_state.test_mode_initialized = True

        # Check if restart is requested
        if st.session_state.get('restart_test_mode', False):
            self.initialize_test_state()
            st.session_state.test_mode_initialized = True
            st.session_state.restart_test_mode = False

        # Display progress
        st.progress(st.session_state.test_state["simulations_completed"] / len(self.simulations))

        if st.session_state.test_state["current_simulation"] < len(self.simulations):
            current_sim = self.simulations[st.session_state.test_state["current_simulation"]]
            st.subheader(f"Simulation {st.session_state.test_state['current_simulation'] + 1}: {current_sim['title']}")
            st.write(current_sim['description'])

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Your response to the client:"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    try:
                        full_response = self.get_client_response(st.session_state.messages, prompt, current_sim)
                        message_placeholder.markdown(full_response)
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        st.error(f"An error occurred while generating the response: {str(e)}")

            if st.button("End Simulation"):
                try:
                    evaluation = self.evaluate_simulation(st.session_state.messages, current_sim)
                    
                    score_match = re.search(r'Score:\s*(\d+)', evaluation)
                    if score_match:
                        score = float(score_match.group(1))
                    else:
                        st.warning("Unable to extract score from evaluation. Using default score of 50.")
                        score = 50.0

                    strength_match = re.search(r'Key Strength:\s*(.+)', evaluation)
                    weakness_match = re.search(r'Area for Improvement:\s*(.+)', evaluation)
                    
                    st.session_state.test_state["scores"].append(score)
                    st.session_state.test_state["chat_histories"].append(st.session_state.messages)
                    
                    st.session_state.test_state["strengths"].append(strength_match.group(1) if strength_match else "No specific strength identified")
                    st.session_state.test_state["weaknesses"].append(weakness_match.group(1) if weakness_match else "No specific area for improvement identified")
                    
                    st.session_state.test_state["simulations_completed"] += 1
                    st.session_state.test_state["current_simulation"] += 1
                    st.session_state.messages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred while evaluating the simulation: {str(e)}")

        else:
            st.success("All simulations completed!")
            if st.session_state.test_state["overall_score"] is None:
                try:
                    overall_score = sum(st.session_state.test_state["scores"]) / len(st.session_state.test_state["scores"])
                    evaluations = []
                    for history, sim in zip(st.session_state.test_state["chat_histories"], self.simulations):
                        try:
                            evaluation = self.evaluate_simulation(history, sim)
                            evaluations.append(evaluation)
                        except Exception as e:
                            st.warning(f"Error during evaluation: {str(e)}")
                            evaluations.append("Evaluation failed due to an error.")
                    
                    evaluations_text = "\n\n".join(evaluations)
                    overall_feedback = self.generate_overall_feedback(st.session_state.test_state["scores"], evaluations_text)
                    st.session_state.test_state["overall_score"] = overall_score
                    st.session_state.test_state["feedback"] = overall_feedback

                    # Save test results
                    test_results = {
                        "date": datetime.datetime.now().isoformat(),
                        "overall_score": overall_score,
                        "individual_scores": st.session_state.test_state["scores"],
                        "strengths": st.session_state.test_state["strengths"],
                        "weaknesses": st.session_state.test_state["weaknesses"],
                        "feedback": overall_feedback
                    }
                    self.save_test_results(test_results)
                except Exception as e:
                    st.error(f"An error occurred while generating overall feedback: {str(e)}")

            st.subheader("Test Results")
            if "overall_score" in st.session_state.test_state and st.session_state.test_state["overall_score"] is not None:
                st.write(f"Overall Score: {st.session_state.test_state['overall_score']:.2f}/100")
                st.write("Feedback:")
                st.write(st.session_state.test_state["feedback"])
            else:
                st.warning("Unable to calculate overall score and feedback due to errors.")

            if st.button("Restart Test Mode"):
                st.session_state.restart_test_mode = True
                st.rerun()

    def display_dashboard(self):
        st.title("Your Progress Dashboard")

        if not st.session_state.test_history:
            st.info("You haven't completed any tests yet. Take a test to see your progress!")
            return

        # Convert test history to a DataFrame for easier analysis
        df = pd.DataFrame(st.session_state.test_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Overall Score Progress
        st.subheader("Overall Score Progress")
        fig = px.line(df, x='date', y='overall_score', title='Your Overall Score Progress')
        st.plotly_chart(fig)

        # Individual Simulation Scores
        st.subheader("Individual Simulation Scores")
        simulation_scores = pd.DataFrame(df['individual_scores'].tolist(), index=df['date']).transpose()
        fig = px.line(simulation_scores, title='Your Scores for Each Simulation')
        st.plotly_chart(fig)

        # Strengths and Weaknesses
        st.subheader("Your Strengths and Areas for Improvement")
        all_strengths = [item for sublist in df['strengths'] for item in sublist]
        all_weaknesses = [item for sublist in df['weaknesses'] for item in sublist]

        col1, col2 = st.columns(2)
        with col1:
            st.write("Top Strengths:")
            strengths_counts = pd.Series(all_strengths).value_counts().head()
            st.bar_chart(strengths_counts)

        with col2:
            st.write("Top Areas for Improvement:")
            weaknesses_counts = pd.Series(all_weaknesses).value_counts().head()
            st.bar_chart(weaknesses_counts)

        # Recent Feedback
        st.subheader("Your Most Recent Feedback")
        st.write(df.iloc[-1]['feedback'])

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Take Test", "View Dashboard"])

    test_manager = TestModeManager()

    if page == "Take Test":
        test_manager.run_test_mode()
    elif page == "View Dashboard":
        test_manager.display_dashboard()

if __name__ == "__main__":
    main()
from openai import OpenAI
import streamlit as st
import random
import time
import json

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

class Question:
    def __init__(self, question, answers, correct_answer, explanation=None):
        self.question = question
        self.answers = answers
        self.correct_answer = correct_answer
        self.explanation = explanation
        
class Quiz:
    def __init__(self):
        self.questions = self.load_or_generate_questions()
        self.initialize_session_state()
        
    def load_or_generate_questions(self):
        if "questions" not in st.session_state:
            st.session_state.questions = [
                # Question(
                #     question="What is the capital of France?",
                #     answers=["Paris", "London", "Berlin", "Madrid"],
                #     correct_answer="Paris",
                #     explanation="Paris is the capital and most populous city of France."
                # ),
                # Question(
                #     question="What is the largest planet in our solar system?",
                #     answers=["Earth", "Mars", "Jupiter", "Saturn"],
                #     correct_answer="Jupiter",
                #     explanation="Jupiter is the largest planet in our solar system and has a mass more than twice that of all the other planets combined."
                # )
            ]
            
        return st.session_state.questions
        
    def initialize_session_state(self):
        if "current_question_index" not in st.session_state:
            st.session_state.current_question_index = 0
        if "scores" not in st.session_state:
            st.session_state.scores = []
        if "history_scores" not in st.session_state:
            st.session_state.history_scores = []
        if "answers_submitted" not in st.session_state:
            st.session_state.answers_submitted = 0
        if "answer_checked" not in st.session_state:
            st.session_state.answer_checked = False
        if "was_correct" not in st.session_state:
            st.session_state.was_correct = False
        if "start_time" not in st.session_state:
            st.session_state.start_time = None
        if "answer_times" not in st.session_state:
            st.session_state.answer_times = []
        if "timer_duration" not in st.session_state:
            st.session_state.timer_duration = None
        if "use_timer" not in st.session_state:
            st.session_state.use_timer = False
        if "score_saved" not in st.session_state:
            st.session_state.score_saved = False
            
    def display_quiz(self):
        if self.questions:
            self.update_progress_bar()
            if st.session_state.answers_submitted < len(self.questions):
                self.display_current_question()
            else:
                self.display_results()
            
    def display_current_question(self):
        question = self.questions[st.session_state.current_question_index]
        total_questions = len(self.questions)
        index = st.session_state.current_question_index


        question_col, feedback_col = st.columns([2, 1])
        
        with question_col:
            st.write(f"**Question {index + 1} of {total_questions}**")
            st.markdown(f"**{question.question}**")
            selected_answer = st.radio(
                "Choose an answer:",
                question.answers,
                key=f"question_{index}"
            )

        if "start_time" not in st.session_state or st.session_state.start_time is None:
            st.session_state.start_time = time.time()

        placeholder = st.empty()

        if st.session_state.use_timer:
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.timer_duration - int(elapsed))

            if not st.session_state.answer_checked:
                if remaining > 0:
                    placeholder.markdown(f"⏳ **Time left:** `{remaining}` seconds")
                    if st.button("Submit", key=f"submit_{index}"):
                        self.check_answer(selected_answer)
                        st.rerun()
                    time.sleep(1)
                    st.rerun()
                else:
                    placeholder.markdown("⏰ **Time's up!**")
                    st.session_state.answer_checked = True
                    st.session_state.was_correct = False
                    st.session_state.scores.append(0)
                    st.session_state.answer_times.append(st.session_state.timer_duration)
        else: 
            if not st.session_state.answer_checked:
                if st.button("Submit", key=f"submit_{index}"):
                    self.check_answer(selected_answer)
                    st.rerun()
                    
        with feedback_col:
            if st.session_state.answer_checked:
                if st.session_state.was_correct:
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Wrong answer!")

                if question.explanation:
                    st.info(question.explanation)
            else:
                st.empty()

        if st.session_state.answer_checked:
            is_last = index >= total_questions - 1
            button_label = "Finish Quiz" if is_last else "Next Question"

            if st.button(button_label, key=f"next_{index}"):
                st.session_state.answers_submitted += 1
                st.session_state.start_time = None

                if not is_last:
                    st.session_state.current_question_index += 1
                    st.session_state.answer_checked = False
                    st.session_state.was_correct = None

                st.rerun()
            
    def check_answer(self, selected_answer):
        time_taken = time.time() - st.session_state.start_time
        st.session_state.answer_times.append(time_taken)
        correct_answer = self.questions[st.session_state.current_question_index].correct_answer
        correct = selected_answer == correct_answer
        st.session_state.answer_checked = True
        st.session_state.was_correct = correct
        st.session_state.scores += [1] if correct else [0]
                    
    
    def display_results(self):
        total_time = sum(st.session_state.answer_times)
        weighted_score = sum([st.session_state.scores[i] / (st.session_state.answer_times[i] if st.session_state.use_timer else 1) * 100 for i in range(len(st.session_state.answer_times))])
                
        st.write(f"Quiz completed in {total_time:.2f}s!")
        st.write(f"Correct answers: {sum(st.session_state.scores)} out of {len(self.questions)}")
        st.write(f"Your score: {weighted_score:.2f} pts")
        
        if weighted_score > max(st.session_state.history_scores, default=0):
            st.success("🏆 Congrats! You set a new high score!")
            st.balloons()
        
        if not st.session_state.score_saved:
            st.session_state.history_scores.append(weighted_score)
            st.session_state.score_saved = True
            
        restart_col, clear_col = st.columns([1, 1])
        with restart_col:
            if st.button("Restart Quiz"):
                self.reset_quiz()
        with clear_col:
            if st.button("Generate New Quiz"):
                self.questions = []
                self.reset_quiz()
            
    def update_progress_bar(self):
        progress = (st.session_state.answers_submitted) / len(self.questions)
        st.progress(progress)
        
    def reset_quiz(self):
        st.session_state.current_question_index = 0
        st.session_state.answers_submitted = 0
        st.session_state.answer_checked = False
        st.session_state.score_saved = False
        st.session_state.start_time = None
        st.session_state.scores = []
        st.session_state.answer_times = []
        st.rerun()
        
def generate_and_append_question(user_prompt, difficulty="moderate", questions_count=10):
    history = ""
    for q in st.session_state.questions:
        history += f"Question: {q.question} Answer: {q.correct_answer}\n"

    # st.markdown(history)

    gpt_prompt = '''
                    You are an AI quiz generator.

                    Generate a list of trivia questions in the following **strict JSON** format:

                    {
                        "Question": "The actual question text goes here?",
                        "Options": ["Option1", "Option2", "Option3", "Option4"],
                        "CorrectAnswer": "TheCorrectAnswer",
                        "Explanation": "A detailed explanation on why the correct answer is correct."
                    }

                    📌 Guidelines:
                    - Return a **JSON array** (list) of individual question objects.
                    - Each object must follow the format exactly.
                    - Each question must have **4 unique options**.
                    - The "CorrectAnswer" must exactly match one of the options.

                    ❗Important:
                    - Return **only one valid JSON object**.
                    - Do **not** wrap the JSON in triple backticks, markdown, or extra commentary.
                    - Do **not** include multiple JSON objects or a list of questions.

                '''
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": gpt_prompt},
                {"role": "user", "content": f"""
                    Create {questions_count} questions about : {user_prompt} that are different from those : {history}. 
                    Make them gradually harder but in general keep it {difficulty.lower()}. Avoid having questions with multiple correct answers."""
                },
            ]
        )
        st.code(response.choices[0].message.content, language="json")
        gpt_response = json.loads(response.choices[0].message.content)
        new_questions = [Question(
            question=q["Question"],
            answers=q["Options"],
            correct_answer=q["CorrectAnswer"],
            explanation=q["Explanation"]
        ) for q in gpt_response]
        st.session_state.questions += new_questions
        st.session_state.quiz.questions = new_questions
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        
if __name__ == "__main__":
    
    loading_messages = [
        "🧠 Summoning trivia wizards...",
        "📚 Flipping through ancient scrolls...",
        "🛠️ Crafting questions with care...",
        "🤖 Asking the AI oracle...",
        "🧐 Cooking up a brain workout...",
        "✨ Brewing knowledge potions...",
        "🔍 Digging up facts and figures...",
        "🚀 Launching quiz shuttle...",
        "📝 Writing mind-bending questions...",
        "⏳ Summoning Socrates and friends..."
    ]
    
    if "quiz_initialized" not in st.session_state:
        st.session_state.quiz = Quiz()
        st.session_state.quiz_initialized = True
    
    
    st.sidebar.title("Trivia Quiz")
    st.sidebar.write("Generate trivia questions and test your knowledge!")
    
    # Options
    st.sidebar.header("Settings")
    difficulty = st.sidebar.selectbox("Select difficulty level:", ["Easy", "Moderate", "Hard"])
    questions_count = st.sidebar.number_input("Number of questions:", min_value=1, max_value=60, value=10, step=5)
    use_timer = st.sidebar.checkbox("Use timer", value=False)
    st.session_state.use_timer = use_timer
    st.session_state.timer_duration = st.sidebar.slider("Timer duration (seconds):", min_value=1, max_value=60, value=15, step=5) if use_timer else None
    if st.session_state.history_scores:
        st.sidebar.divider()
        st.sidebar.header("Leaderboard")
        for i, score in enumerate(sorted(st.session_state.history_scores, reverse=True)):
            st.sidebar.write(f"{i+1}: {score:.2f} pts")
        if st.sidebar.button("Clear Leaderboard"):
            st.session_state.history_scores = []
            st.rerun()
    
    # User Input
    user_input = st.text_input("Enter topics for new questions:")
    
    if st.button("Generate Questions"):
        if user_input:
            with st.spinner(random.choice(loading_messages)):
                generate_and_append_question(user_input, difficulty, questions_count)
        else:
            st.error("Please enter a topic to generate a question.")
            
    st.session_state.quiz.display_quiz()

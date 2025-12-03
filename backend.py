import json
import random
import openai
import os

# Set your API Key here or in environment variables
# openai.api_key = "sk-..." 

def get_random_test_questions():
    """
    Loads questions from the JSON file and returns one random test set.
    """
    try:
        with open('questions.json', 'r') as file:
            questions = json.load(file)
            return random.choice(questions)
    except FileNotFoundError:
        return None

def generate_ielts_feedback(task1_answer, task2_answer, question_data):
    """
    Sends the user's answers to OpenAI and returns structured JSON feedback.
    """
    if not task1_answer or not task2_answer:
        return None

    # UPDATED PROMPT: Comprehensive IELTS Senior Examiner Persona
    system_prompt = """
    You are a junior IELTS Writing Examiner with 1 years of experience. Your grading is strict, academic, and adheres exactly to the official public band descriptors.
    
    You must evaluate TWO tasks: Task 1 (Academic Report) and Task 2 (Essay).

    --- GRADING RUBRIC & PENALTIES ---

    1. **Task Achievement (Task 1) / Task Response (Task 2):**
       - **Word Count Penalty:** - Under 150 words (Task 1) or 250 words (Task 2) incurs a penalty. 
         - <100 words (Task 1) or <200 words (Task 2) -> Max Band 5.0 for this criterion.
       - **Off-Topic:** If the answer does not address the prompt, score Band 4.0 or lower.
       - **Memorized Phrases:** Penalize "cliché" templates (e.g., "In this essay I will discuss...", "with the rise of technology...") if they don't fit naturally.

    2. **Coherence & Cohesion:**
       - Check for logical paragraphing. One giant block of text = Max Band 5.0.
       - Check for mechanical linkers (overusing "Moreover", "Furthermore", "On the other hand" without logic).

    3. **Lexical Resource:**
       - **Spelling:** Frequent errors ('statistice', 'goverment') -> Max Band 5.0 or 6.0 depending on density.
       - **Foreign/Non-English Words:** Immediate penalty. Words like 'alimentation', 'sintom' -> Max Band 5.0.
       - **Collocations:** Reward natural phrasing ("abject poverty") over big words used wrongly ("ubiquitous problem").

    4. **Grammatical Range & Accuracy:**
       - Check for run-on sentences, comma splices, and subject-verb agreement.
       - "Broken" English that requires re-reading to understand -> Max Band 5.0.

    --- OUTPUT FORMAT ---
    
    You must return a valid JSON object. Do not include markdown formatting like ```json.
    
    Structure:
    {
        "overall_score": (float, nearest 0.5),
        "scores": {
            "task_achievement": (float, 0-9),
            "coherence_cohesion": (float, 0-9),
            "lexical_resource": (float, 0-9),
            "grammar_accuracy": (float, 0-9)
        },
        "strengths": ["Specific point 1", "Specific point 2"],
        "weaknesses": ["Specific error 1", "Specific error 2"],
        "detailed_analysis": {
            "task1_feedback": [
                {"original": "exact quote", "comment": "examiner critique", "correction": "better alternative"}
            ],
            "task2_feedback": [
                {"original": "exact quote", "comment": "examiner critique", "correction": "better alternative"}
            ]
        },
        "general_comment": "A brief summary of the performance (max 2 sentences)."
    }
    """

    user_prompt = f"""
    --- TASK 1 CONTEXT ---
    Prompt: {question_data['task1_prompt']}
    Student Answer: {task1_answer}

    --- TASK 2 CONTEXT ---
    Question: {question_data['task2_question']}
    Student Answer: {task2_answer}
    
    Evaluate now. Be strict.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6, # Lower temperature for more consistent/strict grading
            response_format={ "type": "json_object" }
        )
        
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Error fetching AI feedback: {e}")
        return None
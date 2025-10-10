from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime
import torch
from omegaconf import OmegaConf
import urllib.request
import sounddevice as sd
import speech_recognition as sr
import pyttsx3

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in your .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Use the available models from your test
GEMINI_MODELS = [
    'models/gemini-2.0-flash',  # Fast and reliable
    'models/gemini-2.0-flash-001',
    'models/gemini-flash-latest',  # Always points to latest flash
    'models/gemini-pro-latest',    # Always points to latest pro
    'models/gemini-2.0-flash-lite',
    'models/gemini-2.5-flash'
]

# Interview configuration - No fixed question limit
INTERVIEW_CONFIG = {
    "position": "Software Engineer",
    "duration": "flexible",
    "difficulty": "intermediate"
}

# Enhanced System prompt for the AI interviewer
SYSTEM_PROMPT = f"""
You are an expert technical interviewer conducting an interview for a {INTERVIEW_CONFIG['position']} position. 

CRITICAL GUIDELINES:
1. ALWAYS start with asking for the candidate's introduction and which role they have applied for
2. There is NO fixed number of questions - continue until the candidate asks to stop
3. Each question should build upon the previous responses - make it conversational and contextual
4. After the introduction question, ask technical questions based on:
   - Their mentioned skills and experience
   - The role they applied for
   - Their previous answers
5. Ask one question at a time and wait for their response
6. Provide brief, constructive feedback after each answer (1-2 sentences only)
7. Questions should be {INTERVIEW_CONFIG['difficulty']} level and CONCISE
8. Cover topics like: programming concepts, algorithms, data structures, system design, problem-solving
9. Make the interview flow naturally like a real conversation
10. When the candidate says they want to stop or end the interview, provide brief overall feedback
11. KEEP QUESTIONS AND FEEDBACK BRIEF AND TO THE POINT - maximum 2 sentences each
12. Avoid long explanations and detailed examples

Remember: Always personalize questions based on what the candidate has told you about themselves.
The interview continues until the candidate explicitly asks to stop.
"""

# Initialize TTS models
print("🔄 Initializing TTS models...")
url = "https://raw.githubusercontent.com/snakers4/silero-models/master/models.yml"
urllib.request.urlretrieve(url, "latest_silero_models.yml")

models = OmegaConf.load("latest_silero_models.yml")

language = "en"
model_id = "v3_en"
device = torch.device("cpu")

model, _ = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language=language,
    speaker=model_id,
)
model.to(device)

recognizer = sr.Recognizer()
engine = pyttsx3.init()

class InterviewSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.conversation_history = []
        self.question_count = 0
        self.start_time = datetime.now()
        self.is_completed = False
        self.candidate_info = {}  # Store candidate information
        self.all_questions_answers = []  # Store all Q&A for feedback
        
        # Initialize with system prompt
        self.add_message("system", SYSTEM_PROMPT)
        
    def add_message(self, role, content):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def extract_candidate_info(self, response):
        """Extract candidate information from their responses"""
        # Simple extraction - you can make this more sophisticated
        if "applied for" in response.lower() or "role" in response.lower():
            self.candidate_info['applied_role'] = response
        if "introduction" in response.lower() or "name" in response.lower() or "experience" in response.lower():
            self.candidate_info['introduction'] = response
    
    def add_qa_pair(self, question, answer):
        """Store question-answer pair for feedback"""
        self.all_questions_answers.append({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        })

# Store active interview sessions
interview_sessions = {}

def find_working_model():
    """Find a working Gemini model from the available list"""
    print("🔍 Searching for working model...")
    
    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            # Test with a simple prompt
            response = model.generate_content("Say 'Hello' in one word.")
            if response.text:
                print(f"✅ Successfully connected to model: {model_name}")
                return model_name
        except Exception as e:
            print(f"❌ Model {model_name} failed: {e}")
            continue
    
    # If no predefined model works, try to find any available model
    try:
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                try:
                    test_model = genai.GenerativeModel(model.name)
                    response = test_model.generate_content("Test")
                    if response.text:
                        print(f"✅ Successfully connected to available model: {model.name}")
                        return model.name
                except:
                    continue
    except Exception as e:
        print(f"Error searching for models: {e}")
    
    return None

# Find and set the working model
WORKING_MODEL = find_working_model()
if not WORKING_MODEL:
    raise Exception("No working Gemini model found. Please check your API key and region.")

print(f"🎯 Using model: {WORKING_MODEL}")

def generate_overall_feedback(conversation_history, candidate_info, qa_pairs):
    """Generate brief comprehensive feedback after interview ends"""
    try:
        model = genai.GenerativeModel(WORKING_MODEL)
        
        # Prepare conversation summary for feedback
        qa_summary = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}\n" for qa in qa_pairs])
        
        feedback_prompt = f"""
Based on the following technical interview conversation, provide brief overall feedback for the candidate.

Candidate Information:
{json.dumps(candidate_info, indent=2)}

Interview Conversation Summary:
{qa_summary}

Please provide brief structured feedback covering:
1. Technical Knowledge & Skills
2. Problem-Solving Approach
3. Communication Skills
4. Key Strengths
5. Areas for Improvement

Make the feedback constructive and professional but VERY CONCISE (maximum 100 words).
"""

        response = model.generate_content(feedback_prompt)
        return response.text.strip() if response.text else "Thank you for your time. We appreciate your participation in this interview."
    
    except Exception as e:
        print(f"Feedback generation error: {e}")
        return "Thank you for completing the interview. Your responses have been recorded and will be reviewed by our team."

def generate_ai_response(conversation_history, is_final_feedback=False):
    """Generate response using Gemini API with contextual awareness"""
    try:
        # Create model with working model name
        model = genai.GenerativeModel(WORKING_MODEL)
        
        # Prepare conversation context
        context_messages = []
        for msg in conversation_history:
            if msg['role'] == 'system':
                context_messages.append(f"System Instructions: {msg['content']}")
            elif msg['role'] == 'user':
                context_messages.append(f"Candidate: {msg['content']}")
            elif msg['role'] == 'assistant':
                context_messages.append(f"Interviewer: {msg['content']}")
        
        context = "\n".join(context_messages)
        
        if is_final_feedback:
            # Generate farewell message when interview ends
            prompt = f"""
The candidate has decided to end the interview. Please provide a brief polite closing message thanking them for their time.

Previous conversation:
{context}

Interviewer:"""
        else:
            # Enhanced prompt for contextual questioning
            prompt = f"""
You are conducting a technical interview. Here's the conversation so far:

{context}

IMPORTANT INSTRUCTIONS:
1. Analyze the candidate's previous responses to ask relevant follow-up questions
2. If this is the beginning, ask for introduction and applied role
3. Build upon their technical skills, experience, and previous answers
4. Ask only ONE question at a time
5. Provide brief, constructive feedback on their previous answer before asking the next question (1-2 sentences only)
6. Make it conversational and natural
7. Continue until the candidate asks to stop/end the interview
8. KEEP ALL QUESTIONS AND FEEDBACK CONCISE - maximum 2 sentences each
9. Avoid long explanations and detailed examples

Current conversation flow:
"""

        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
        else:
            return "Thank you for that response. Let me ask you another question based on what you've shared."
    
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        # Contextual fallback responses
        fallback_responses = [
            "Thank you for sharing that. What would you say is the most challenging aspect?",
            "I appreciate your response. Could you elaborate briefly?",
            "That's interesting. What factors would you consider?",
        ]
        import random
        return random.choice(fallback_responses)

def should_end_interview(user_input):
    """Check if user wants to end the interview"""
    stop_keywords = ['stop', 'no more', 'thank you that\'s it']
    return any(keyword in user_input.lower() for keyword in stop_keywords)

# ========== SPEECH ROUTES ==========

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "Hello from Silero TTS")
    speaker = data.get("speaker", "en_10")
    sample_rate = 24000

    # Generate audio
    audio = model.apply_tts(
        text=text,
        speaker=speaker,
        sample_rate=sample_rate,
        put_accent=True,
        put_yo=True,
    )

    # Play audio automatically
    sd.play(audio, sample_rate)
    sd.wait()

    return jsonify({"status": "ok", "text": text, "speaker": speaker})


@app.route("/stt", methods=["GET"])
def stt():
    with sr.Microphone() as source:
        print("🎤 Speak something...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("✅ You said:", text)
        return jsonify({"status": "ok", "transcription": text})
    except sr.UnknownValueError:
        return jsonify({"status": "error", "message": "Could not understand audio"})
    except sr.RequestError as e:
        return jsonify({"status": "error", "message": f"API Error: {e}"})

# ========== INTERVIEW ROUTES ==========

@app.route('/api/start-interview', methods=['POST'])
def start_interview():
    """Start a new interview session"""
    try:
        session_id = str(uuid.uuid4())
        interview_session = InterviewSession(session_id)
        interview_sessions[session_id] = interview_session
        
        # Generate initial greeting and first question (introduction)
        initial_response = generate_ai_response(interview_session.conversation_history)
        interview_session.add_message("assistant", initial_response)
        interview_session.question_count += 1
        
        return jsonify({
            'session_id': session_id,
            'message': initial_response,
            'question_number': interview_session.question_count,
            'status': 'started',
            'has_question_limit': False
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/respond', methods=['POST'])
def respond_to_question():
    """Process candidate's response and get next question or end interview"""
    try:
        data = request.json
        session_id = data.get('session_id')
        candidate_response = data.get('response', '').strip()
        
        if not session_id or session_id not in interview_sessions:
            return jsonify({'error': 'Invalid session ID'}), 400
        
        if not candidate_response:
            return jsonify({'error': 'Response is required'}), 400
        
        interview_session = interview_sessions[session_id]
        
        # Check if interview is completed
        if interview_session.is_completed:
            return jsonify({'error': 'Interview already completed'}), 400
        
        # Check if user wants to end the interview
        if should_end_interview(candidate_response):
            interview_session.is_completed = True
            
            # Store the last question-answer pair if available
            if interview_session.conversation_history and len(interview_session.conversation_history) >= 2:
                last_question = interview_session.conversation_history[-2]['content'] if interview_session.conversation_history[-2]['role'] == 'assistant' else "Introduction question"
                interview_session.add_qa_pair(last_question, candidate_response)
            
            # Generate overall feedback
            feedback = generate_overall_feedback(
                interview_session.conversation_history,
                interview_session.candidate_info,
                interview_session.all_questions_answers
            )
            
            # Add final message
            farewell_message = generate_ai_response(interview_session.conversation_history, is_final_feedback=True)
            interview_session.add_message("assistant", farewell_message)
            
            return jsonify({
                'session_id': session_id,
                'message': farewell_message,
                'feedback': feedback,
                'question_number': interview_session.question_count,
                'total_questions_asked': interview_session.question_count,
                'status': 'completed',
                'is_final_message': True,
                'candidate_info': interview_session.candidate_info,
                'duration_minutes': round((datetime.now() - interview_session.start_time).total_seconds() / 60, 2)
            })
        
        # Extract candidate information from response
        interview_session.extract_candidate_info(candidate_response)
        
        # Store the previous question and current answer for feedback
        if interview_session.conversation_history and interview_session.conversation_history[-1]['role'] == 'assistant':
            last_question = interview_session.conversation_history[-1]['content']
            interview_session.add_qa_pair(last_question, candidate_response)
        
        # Add candidate's response to history
        interview_session.add_message("user", candidate_response)
        
        # Generate next question with contextual awareness
        ai_response = generate_ai_response(interview_session.conversation_history)
        interview_session.add_message("assistant", ai_response)
        interview_session.question_count += 1
        
        return jsonify({
            'session_id': session_id,
            'message': ai_response,
            'question_number': interview_session.question_count,
            'status': 'in_progress',
            'candidate_info': interview_session.candidate_info,
            'has_question_limit': False
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/end-interview/<session_id>', methods=['POST'])
def end_interview(session_id):
    """End an interview session manually"""
    if session_id not in interview_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    interview_session = interview_sessions[session_id]
    
    if not interview_session.is_completed:
        interview_session.is_completed = True
        
        # Generate overall feedback
        feedback = generate_overall_feedback(
            interview_session.conversation_history,
            interview_session.candidate_info,
            interview_session.all_questions_answers
        )
        
        # Generate farewell message
        farewell_message = "Thank you for your participation in this interview. The session has been concluded."
        
        return jsonify({
            'message': farewell_message,
            'feedback': feedback,
            'session_id': session_id,
            'status': 'ended',
            'total_questions_asked': interview_session.question_count,
            'candidate_info': interview_session.candidate_info,
            'duration_minutes': round((datetime.now() - interview_session.start_time).total_seconds() / 60, 2)
        })
    
    return jsonify({'error': 'Interview already completed'}), 400

@app.route('/api/interview-status/<session_id>', methods=['GET'])
def get_interview_status(session_id):
    """Get current status of an interview session"""
    if session_id not in interview_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    interview_session = interview_sessions[session_id]
    
    return jsonify({
        'session_id': session_id,
        'question_number': interview_session.question_count,
        'is_completed': interview_session.is_completed,
        'start_time': interview_session.start_time.isoformat(),
        'duration_minutes': round((datetime.now() - interview_session.start_time).total_seconds() / 60, 2),
        'candidate_info': interview_session.candidate_info,
        'has_question_limit': False
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'Interview API',
        'model': WORKING_MODEL
    })

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models"""
    try:
        models = genai.list_models()
        available_models = []
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                available_models.append(model.name)
        return jsonify({'available_models': available_models, 'current_model': WORKING_MODEL})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== HOME ROUTE ==========

@app.route("/")
def home():
    return jsonify({
        "message": "Speech and Interview Server is running!",
        "routes": {
            "POST /tts": "Convert text to speech",
            "GET /stt": "Convert microphone speech to text",
            "POST /api/start-interview": "Start a new interview session",
            "POST /api/respond": "Respond to interview question",
            "GET /api/interview-status/<session_id>": "Get interview status",
            "POST /api/end-interview/<session_id>": "End interview session",
            "GET /api/health": "Health check",
            "GET /api/models": "Get available models"
        }
    })

# ========== RUN SERVER ==========

if __name__ == "__main__":
    port = 5000
    print(f"🚀 Combined Speech and Interview Server running at http://127.0.0.1:{port}")
    print(f"🎯 Using Gemini model: {WORKING_MODEL}")
    print("📝 Available endpoints:")
    print("   GET  /")
    print("   POST /tts")
    print("   GET  /stt")
    print("   POST /api/start-interview")
    print("   POST /api/respond")
    print("   GET  /api/interview-status/<session_id>")
    print("   POST /api/end-interview/<session_id>")
    print("   GET  /api/health")
    print("   GET  /api/models")
    print("\n✨ Features:")
    print("   - Text-to-Speech (TTS) with Silero")
    print("   - Speech-to-Text (STT) with Google Speech Recognition")
    print("   - AI-powered interview sessions with Gemini")
    print("   - No question limit - interview continues until you stop")
    print("   - Automatic brief feedback at the end")
    
    app.run(host="0.0.0.0", port=port, debug=True)
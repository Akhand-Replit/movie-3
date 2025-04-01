import streamlit as st
import requests
import json
import time
import google.generativeai as genai

# Set page configuration
st.set_page_config(
    page_title="SVOMO RECOMMENDATION",
    page_icon="🎬",
    layout="centered"
)

# Load secrets
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Apply custom styling for retro UI
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
        
        * {
            font-family: 'VT323', monospace;
        }
        
        h1, h2, h3 {
            font-family: 'Press Start 2P', cursive;
            color: #ff00ff;
            text-shadow: 2px 2px #00ffff;
        }
        
        .stButton button {
            background-color: #ff00ff;
            color: black;
            border: 2px solid #00ffff;
            border-radius: 0px;
            font-family: 'VT323', monospace;
            text-transform: uppercase;
            font-size: 1.2rem;
            margin: 5px 0;
            transition: all 0.3s;
        }
        
        .stButton button:hover {
            background-color: #00ffff;
            color: black;
            border: 2px solid #ff00ff;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 0, 255, 0.5);
        }
        
        .retro-card {
            border: 2px solid #ff00ff;
            background-color: rgba(0, 0, 0, 0.7);
            padding: 20px;
            margin: 10px 0;
            box-shadow: 5px 5px 0px #00ffff;
        }
        
        .title-text {
            font-family: 'Press Start 2P', cursive;
            font-size: 2.5em;
            color: #ff00ff;
            text-shadow: 3px 3px #00ffff;
            text-align: center;
            margin-bottom: 30px;
        }
        
        .question-text {
            font-size: 1.5em;
            color: #00ffff;
            margin-bottom: 20px;
        }
        
        .option-text {
            font-size: 1.2em;
            color: white;
        }
        
        /* Retro grid background */
        .stApp {
            background-image: 
                linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)),
                linear-gradient(90deg, rgba(255, 0, 255, 0.2) 1px, transparent 1px),
                linear-gradient(0deg, rgba(0, 255, 255, 0.2) 1px, transparent 1px);
            background-size: 100% 100%, 30px 30px, 30px 30px;
            background-color: #000020;
        }
        
        /* Movie card styling */
        .movie-card {
            border: 2px solid #ff00ff;
            background-color: rgba(0, 0, 0, 0.7);
            padding: 15px;
            margin: 10px;
            box-shadow: 5px 5px 0px #00ffff;
            transition: transform 0.3s;
        }
        
        .movie-card:hover {
            transform: translateY(-5px);
            box-shadow: 8px 8px 0px #00ffff;
        }
        
        .movie-title {
            font-family: 'Press Start 2P', cursive;
            font-size: 1em;
            color: #ff00ff;
            margin: 10px 0;
        }
        
        .movie-year {
            color: #00ffff;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .movie-overview {
            color: white;
            font-size: 1.2em;
            margin-top: 10px;
        }
        
        /* Loading animation */
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 40px 0;
        }
        
        .loading-text {
            color: #ff00ff;
            font-size: 24px;
            margin-bottom: 20px;
            font-family: 'Press Start 2P', cursive;
        }
        
        .loading-dots {
            display: flex;
        }
        
        .loading-dot {
            width: 20px;
            height: 20px;
            margin: 0 10px;
            border-radius: 50%;
            background-color: #00ffff;
            animation: loading-dot-animation 1.5s infinite ease-in-out;
        }
        
        .loading-dot:nth-child(1) {
            animation-delay: 0s;
        }
        
        .loading-dot:nth-child(2) {
            animation-delay: 0.3s;
        }
        
        .loading-dot:nth-child(3) {
            animation-delay: 0.6s;
        }
        
        @keyframes loading-dot-animation {
            0%, 100% {
                transform: scale(0.5);
                background-color: #00ffff;
            }
            50% {
                transform: scale(1.5);
                background-color: #ff00ff;
            }
        }
        
        /* Credits section */
        .credits {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            border-top: 1px solid #ff00ff;
        }
        
        .credits img {
            margin: 0 10px;
            max-height: 30px;
        }
        
        /* Blinking cursor effect */
        .blinking-cursor {
            animation: blink 1s infinite;
            display: inline-block;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'step' not in st.session_state:
        st.session_state.step = 'welcome'
    if 'persona' not in st.session_state:
        st.session_state.persona = None
    if 'answers' not in st.session_state:
        st.session_state.answers = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = []

# Display loading animation
def show_loading(text="Loading..."):
    st.markdown(f"""
    <div class="loading-container">
        <div class="loading-text">{text}</div>
        <div class="loading-dots">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Function to communicate with Gemini API
def ask_gemini(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    return response.text

# Function to generate personalized questions based on persona
def generate_questions(persona):
    prompt = f"""
    Generate a sequence of 8 personalized questions to recommend movies or shows based on this persona: {persona}.
    
    Each question should have 2-4 options for the user to choose from. Format your response as a JSON array of objects, 
    where each object has 'question' and 'options' fields. The options should be an array of strings.
    
    Make sure questions cover: mood, watching companions, available time, content preferences (movie/series length), 
    thematic interests, age of content (new releases vs classics), and preferred languages/regions.
    
    Example format:
    [
        {{
            "question": "Are you watching alone or with someone?",
            "options": ["Alone", "With friends", "With family", "With a date"]
        }}
    ]
    
    IMPORTANT: Return ONLY valid JSON without any explanation or additional text.
    """
    
    try:
        response = ask_gemini(prompt)
        return json.loads(response)
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

# Function to get movie recommendations based on user responses
def get_recommendations(persona, questions, answers):
    # Create a detailed prompt for Gemini to generate recommendations
    answers_text = "\n".join([f"Q: {q['question']}\nA: {a}" for q, a in zip(questions, answers)])
    
    prompt = f"""
    Based on the following user persona and preferences, recommend exactly 3 movies or TV shows.
    
    User Persona: {persona}
    
    User Preferences:
    {answers_text}
    
    For each recommendation, provide:
    1. Title (exactly as it would appear in TheMovieDB)
    2. Media type ("movie" or "tv")
    3. A brief explanation of why this recommendation matches the user's preferences (2-3 sentences max)
    
    Format your response as a JSON array of objects with 'title', 'type', and 'reason' fields.
    
    Example:
    [
        {{
            "title": "Inception",
            "type": "movie",
            "reason": "This mind-bending sci-fi thriller matches your interest in complex plots and psychological themes."
        }}
    ]
    
    IMPORTANT: Return ONLY valid JSON without any explanation or additional text.
    """
    
    try:
        response = ask_gemini(prompt)
        return json.loads(response)
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []

# Function to search for movie/TV show details from TMDB
def search_tmdb(title, media_type):
    url = f"https://api.themoviedb.org/3/search/{media_type}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }
    params = {
        "query": title,
        "include_adult": "false",
        "language": "en-US",
        "page": "1"
    }
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]  # Return the first (most relevant) result
    return None

# Function to get full details for a movie or TV show
def get_tmdb_details(item_id, media_type):
    url = f"https://api.themoviedb.org/3/{media_type}/{item_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {TMDB_API_KEY}"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# Function to generate AI description for a movie/show
def generate_ai_description(title, overview, media_type, reason):
    prompt = f"""
    Create a brief, engaging description for this {media_type}:
    
    Title: {title}
    Original Overview: {overview}
    Recommendation Reason: {reason}
    
    Write a concise (maximum 2-3 sentences) and appealing description that highlights why this would be enjoyable
    based on the recommendation reason. Use a retro-futuristic tone with vibrant language.
    """
    
    try:
        response = ask_gemini(prompt)
        return response
    except Exception as e:
        return overview[:150] + "..."  # Fallback to truncated original overview

# Display welcome screen
def show_welcome():
    st.markdown("""
    <div class="title-text">
        SVOMO RECOMMENDATION<span class="blinking-cursor">_</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="retro-card">
        <div class="question-text">Welcome to the ultimate movie recommendation system</div>
        <div class="option-text">
            Select your entertainment preference to begin your personalized journey:
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        persona_options = [
            "Anime Fan", 
            "Hollywood Movie Enthusiast", 
            "Bollywood Fan", 
            "K-Drama Lover", 
            "TV Series Binger",
            "Indie Film Appreciator"
        ]
        
        for persona in persona_options:
            if st.button(persona, key=f"persona_{persona}", use_container_width=True):
                st.session_state.persona = persona
                st.session_state.step = 'generating_questions'
                st.rerun()
    
    # Credits
    st.markdown("""
    <div class="credits">
        <p style="color: #00ffff; font-size: 1.2em;">Powered by Google Gemini AI | Movie data from TheMovieDB</p>
        <div>
            <img src="https://www.gstatic.com/lamda/images/gemini_ai_logo_70e467c4f0c37.svg" alt="Gemini AI">
            <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" alt="TMDB">
        </div>
    </div>
    """, unsafe_allow_html=True)

# Generate questions based on selected persona
def generate_persona_questions():
    show_loading("Generating personalized questions...")
    
    # Generate questions
    questions = generate_questions(st.session_state.persona)
    
    if questions:
        st.session_state.questions = questions
        st.session_state.step = 'asking_questions'
    else:
        st.error("Failed to generate questions. Please try again.")
        st.session_state.step = 'welcome'
    
    st.rerun()

# Display current question and options
def show_question():
    current_q = st.session_state.current_question
    
    if current_q < len(st.session_state.questions):
        question = st.session_state.questions[current_q]
        
        # Progress indicator
        progress = (current_q + 1) / len(st.session_state.questions)
        st.progress(progress)
        
        st.markdown("""
        <div class="title-text" style="font-size: 1.8em;">
            SVOMO RECOMMENDATION<span class="blinking-cursor">_</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="retro-card">
            <div class="question-text">Question {current_q + 1}/{len(st.session_state.questions)}</div>
            <div class="question-text">{question['question']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            for option in question['options']:
                if st.button(option, key=f"option_{option}", use_container_width=True):
                    st.session_state.answers.append(option)
                    st.session_state.current_question += 1
                    
                    # Check if all questions are answered
                    if st.session_state.current_question >= len(st.session_state.questions):
                        st.session_state.step = 'generating_recommendations'
                    
                    st.rerun()
    else:
        st.session_state.step = 'generating_recommendations'
        st.rerun()

# Generate and display movie recommendations
def generate_recommendations():
    show_loading("Analyzing your preferences and finding perfect recommendations...")
    
    # Get AI recommendations
    recommendations = get_recommendations(
        st.session_state.persona, 
        st.session_state.questions, 
        st.session_state.answers
    )
    
    if not recommendations:
        st.error("Failed to generate recommendations. Please try again.")
        if st.button("Try Again"):
            st.session_state.step = 'welcome'
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()
        return
    
    # Fetch detailed information from TMDB
    detailed_recommendations = []
    
    for rec in recommendations:
        title = rec.get('title')
        media_type = rec.get('type', 'movie')  # Default to movie if not specified
        reason = rec.get('reason', '')
        
        # Search for the title in TMDB
        result = search_tmdb(title, media_type)
        
        if result:
            item_id = result.get('id')
            # Get full details
            details = get_tmdb_details(item_id, media_type)
            
            if details:
                # Extract relevant information
                poster_path = details.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg"
                
                overview = details.get('overview', '')
                
                # For movies, get release year; for TV shows, get first air date year
                year = ""
                if media_type == 'movie' and 'release_date' in details:
                    year = details['release_date'][:4] if details.get('release_date') else ''
                elif media_type == 'tv' and 'first_air_date' in details:
                    year = details['first_air_date'][:4] if details.get('first_air_date') else ''
                
                # Generate AI description
                ai_description = generate_ai_description(title, overview, media_type, reason)
                
                detailed_recommendations.append({
                    'title': details.get('title') if media_type == 'movie' else details.get('name'),
                    'poster_url': poster_url,
                    'year': year,
                    'overview': overview,
                    'ai_description': ai_description,
                    'media_type': media_type.title(),
                    'reason': reason
                })
        
        # If no TMDB result, create a fallback recommendation
        if not result:
            detailed_recommendations.append({
                'title': title,
                'poster_url': "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg",
                'year': '',
                'overview': '',
                'ai_description': reason,
                'media_type': media_type.title(),
                'reason': reason
            })
    
    st.session_state.recommendations = detailed_recommendations
    st.session_state.step = 'show_recommendations'
    st.rerun()

# Display movie recommendations
def show_recommendations():
    st.markdown("""
    <div class="title-text">
        SVOMO RECOMMENDATION<span class="blinking-cursor">_</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="retro-card">
        <div class="question-text">Your Personalized Recommendations</div>
        <div class="option-text">
            Based on your preferences, here are the top 3 picks just for you:
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display recommendations in cards
    cols = st.columns(3)
    
    for i, rec in enumerate(st.session_state.recommendations):
        with cols[i]:
            st.markdown(f"""
            <div class="movie-card">
                <div style="text-align: center;">
                    <img src="{rec['poster_url']}" style="max-width: 100%; height: auto; border: 2px solid #ff00ff;">
                </div>
                <div class="movie-title">{rec['title']}</div>
                <div class="movie-year">{rec['year']} | {rec['media_type']}</div>
                <div class="movie-overview">{rec['ai_description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show additional details in expandable section
            with st.expander("Why this recommendation?"):
                st.write(rec['reason'])
                if rec['overview']:
                    st.write("**Original Overview:**")
                    st.write(rec['overview'])
    
    # Restart button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Over", use_container_width=True):
            st.session_state.step = 'welcome'
            st.session_state.persona = None
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.session_state.questions = []
            st.session_state.recommendations = []
            st.rerun()
    
    # Credits
    st.markdown("""
    <div class="credits">
        <p style="color: #00ffff; font-size: 1.2em;">Powered by Google Gemini AI | Movie data from TheMovieDB</p>
        <div>
            <img src="https://www.gstatic.com/lamda/images/gemini_ai_logo_70e467c4f0c37.svg" alt="Gemini AI">
            <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" alt="TMDB">
        </div>
    </div>
    """, unsafe_allow_html=True)

# Generate questions based on selected persona
def generate_persona_questions():
    show_loading("Generating personalized questions...")
    
    # Generate questions
    questions = generate_questions(st.session_state.persona)
    
    if questions:
        st.session_state.questions = questions
        st.session_state.step = 'asking_questions'
    else:
        st.error("Failed to generate questions. Please try again.")
        st.session_state.step = 'welcome'
    
    st.rerun()

# Display current question and options
def show_question():
    current_q = st.session_state.current_question
    
    if current_q < len(st.session_state.questions):
        question = st.session_state.questions[current_q]
        
        # Progress indicator
        progress = (current_q + 1) / len(st.session_state.questions)
        st.progress(progress)
        
        st.markdown("""
        <div class="title-text" style="font-size: 1.8em;">
            SVOMO RECOMMENDATION<span class="blinking-cursor">_</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="retro-card">
            <div class="question-text">Question {current_q + 1}/{len(st.session_state.questions)}</div>
            <div class="question-text">{question['question']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            for option in question['options']:
                if st.button(option, key=f"option_{option}", use_container_width=True):
                    st.session_state.answers.append(option)
                    st.session_state.current_question += 1
                    
                    # Check if all questions are answered
                    if st.session_state.current_question >= len(st.session_state.questions):
                        st.session_state.step = 'generating_recommendations'
                    
                    st.rerun()
    else:
        st.session_state.step = 'generating_recommendations'
        st.rerun()

# Generate and display movie recommendations
def generate_recommendations():
    show_loading("Analyzing your preferences and finding perfect recommendations...")
    
    # Get AI recommendations
    recommendations = get_recommendations(
        st.session_state.persona, 
        st.session_state.questions, 
        st.session_state.answers
    )
    
    if not recommendations:
        st.error("Failed to generate recommendations. Please try again.")
        if st.button("Try Again"):
            st.session_state.step = 'welcome'
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.rerun()
        return
    
    # Fetch detailed information from TMDB
    detailed_recommendations = []
    
    for rec in recommendations:
        title = rec.get('title')
        media_type = rec.get('type', 'movie')  # Default to movie if not specified
        reason = rec.get('reason', '')
        
        # Search for the title in TMDB
        result = search_tmdb(title, media_type)
        
        if result:
            item_id = result.get('id')
            # Get full details
            details = get_tmdb_details(item_id, media_type)
            
            if details:
                # Extract relevant information
                poster_path = details.get('poster_path')
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg"
                
                overview = details.get('overview', '')
                
                # For movies, get release year; for TV shows, get first air date year
                year = ""
                if media_type == 'movie' and 'release_date' in details:
                    year = details['release_date'][:4] if details.get('release_date') else ''
                elif media_type == 'tv' and 'first_air_date' in details:
                    year = details['first_air_date'][:4] if details.get('first_air_date') else ''
                
                # Generate AI description
                ai_description = generate_ai_description(title, overview, media_type, reason)
                
                detailed_recommendations.append({
                    'title': details.get('title') if media_type == 'movie' else details.get('name'),
                    'poster_url': poster_url,
                    'year': year,
                    'overview': overview,
                    'ai_description': ai_description,
                    'media_type': media_type.title(),
                    'reason': reason
                })
        
        # If no TMDB result, create a fallback recommendation
        if not result:
            detailed_recommendations.append({
                'title': title,
                'poster_url': "https://i.ibb.co/s9ZYS5wk/45e6544ed099.jpg",
                'year': '',
                'overview': '',
                'ai_description': reason,
                'media_type': media_type.title(),
                'reason': reason
            })
    
    st.session_state.recommendations = detailed_recommendations
    st.session_state.step = 'show_recommendations'
    st.rerun()

# Display movie recommendations
def show_recommendations():
    st.markdown("""
    <div class="title-text">
        SVOMO RECOMMENDATION<span class="blinking-cursor">_</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="retro-card">
        <div class="question-text">Your Personalized Recommendations</div>
        <div class="option-text">
            Based on your preferences, here are the top 3 picks just for you:
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display recommendations in cards
    cols = st.columns(3)
    
    for i, rec in enumerate(st.session_state.recommendations):
        with cols[i]:
            st.markdown(f"""
            <div class="movie-card">
                <div style="text-align: center;">
                    <img src="{rec['poster_url']}" style="max-width: 100%; height: auto; border: 2px solid #ff00ff;">
                </div>
                <div class="movie-title">{rec['title']}</div>
                <div class="movie-year">{rec['year']} | {rec['media_type']}</div>
                <div class="movie-overview">{rec['ai_description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show additional details in expandable section
            with st.expander("Why this recommendation?"):
                st.write(rec['reason'])
                if rec['overview']:
                    st.write("**Original Overview:**")
                    st.write(rec['overview'])
    
    # Restart button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Over", use_container_width=True):
            st.session_state.step = 'welcome'
            st.session_state.persona = None
            st.session_state.answers = []
            st.session_state.current_question = 0
            st.session_state.questions = []
            st.session_state.recommendations = []
            st.rerun()
    
    # Credits
    st.markdown("""
    <div class="credits">
        <p style="color: #00ffff; font-size: 1.2em;">Powered by Google Gemini AI | Movie data from TheMovieDB</p>
        <div>
            <img src="https://www.gstatic.com/lamda/images/gemini_ai_logo_70e467c4f0c37.svg" alt="Gemini AI">
            <img src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg" alt="TMDB">
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main app flow
def main():
    # Initialize session state
    init_session_state()
    
    # Add custom CSS
    load_css()
    
    # Route to the appropriate step
    if st.session_state.step == 'welcome':
        show_welcome()
    elif st.session_state.step == 'generating_questions':
        generate_persona_questions()
    elif st.session_state.step == 'asking_questions':
        show_question()
    elif st.session_state.step == 'generating_recommendations':
        generate_recommendations()
    elif st.session_state.step == 'show_recommendations':
        show_recommendations()

if __name__ == "__main__":
    main()

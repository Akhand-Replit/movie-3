import streamlit as st
import requests
import json
import time
import google.generativeai as genai

# Set page configuration
st.set_page_config(
    page_title="SVOMO RECOMMENDATION",
    page_icon="🎬",
    layout="wide"
)

# Load secrets with proper error handling
try:
    TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
except Exception as e:
    st.error("TMDB API key not found in secrets. Please check your secrets.toml file.")
    TMDB_API_KEY = "missing"

try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    # Configure Gemini API right away to catch errors early
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"Error configuring Gemini API: {e}. Please check your secrets.toml file.")
    GEMINI_API_KEY = "missing"

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
    if 'debug_info' not in st.session_state:
        st.session_state.debug_info = ""
    if 'retry_count' not in st.session_state:
        st.session_state.retry_count = 0

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
    try:
        # Check if API key is missing
        if GEMINI_API_KEY == "missing":
            st.session_state.debug_info = "Gemini API key is missing. Using fallback content."
            return '{"error": "API key missing"}'
            
        # Create model and generate content with error handling
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Safety check before API call
        if not model:
            st.session_state.debug_info = "Failed to create Gemini model"
            return '{"error": "Model creation failed"}'
            
        # Generate content with timeout
        response = model.generate_content(prompt)
        
        # Check if response is valid
        if response and hasattr(response, 'text'):
            return response.text
        else:
            st.session_state.debug_info = "Empty or invalid response from Gemini"
            return '{"error": "Invalid response"}'
            
    except Exception as e:
        st.session_state.debug_info = f"Error in ask_gemini: {str(e)}"
        # If there's an error, return a placeholder response that can be handled by the caller
        return '{"error": "Failed to generate content"}'

# Function to generate personalized questions based on persona
def generate_questions(persona):
    # Fallback questions in case API fails
    fallback_questions = [
        {
            "question": "Are you watching alone or with someone?",
            "options": ["Alone", "With friends", "With family", "With a date"]
        },
        {
            "question": "What mood are you in right now?",
            "options": ["Happy/Upbeat", "Thoughtful/Reflective", "Need a good laugh", "Want to be thrilled"]
        },
        {
            "question": "How much time do you have?",
            "options": ["Under 2 hours", "2-3 hours", "I have all night", "Looking for a series to binge"]
        },
        {
            "question": "What themes interest you most?",
            "options": ["Action/Adventure", "Romance", "Mystery/Thriller", "Sci-Fi/Fantasy"]
        },
        {
            "question": "Do you prefer new releases or classics?",
            "options": ["Latest releases only", "Recent (last 5 years)", "Classics (pre-2000)", "I don't mind"]
        },
        {
            "question": "Any specific languages you prefer?",
            "options": ["English only", "Don't mind subtitles", "Non-English specifically", "No preference"]
        },
        {
            "question": "Do you like intense content or lighter fare?",
            "options": ["Light and fun", "Moderately intense", "Dark and serious", "Thought-provoking"]
        },
        {
            "question": "What's your preference for visuals?",
            "options": ["Beautiful cinematography", "Special effects", "Simple storytelling", "Artistic style"]
        }
    ]
    
    # If persona is anime fan, replace with anime-specific questions
    if persona == "Anime Fan":
        fallback_questions[3] = {
            "question": "What anime genres do you enjoy most?",
            "options": ["Shonen/Action", "Slice of Life", "Romance/Drama", "Fantasy/Isekai"]
        }
    
    # Try to get AI-generated questions, fall back if it fails
    try:
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
        
        st.session_state.debug_info = "Attempting to call Gemini API..."
        response = ask_gemini(prompt)
        st.session_state.debug_info = f"Gemini API response received: {response[:100]}..."
        
        parsed_response = json.loads(response)
        st.session_state.debug_info = "Successfully parsed JSON response"
        
        # Verify the structure is correct
        if (isinstance(parsed_response, list) and 
            all('question' in q and 'options' in q for q in parsed_response) and
            len(parsed_response) >= 3):
            return parsed_response
        else:
            st.session_state.debug_info = "Response had incorrect structure, using fallback"
            return fallback_questions
            
    except Exception as e:
        st.session_state.debug_info = f"Error in generate_questions: {str(e)}"
        st.error(f"Error generating questions: {e}")
        return fallback_questions

# Function to get movie recommendations based on user responses
def get_recommendations(persona, questions, answers):
    # Default recommendations for different personas if API fails
    default_recommendations = {
        "Anime Fan": [
            {"title": "Spirited Away", "type": "movie", "reason": "A classic anime film with beautiful animation and a compelling story."},
            {"title": "Attack on Titan", "type": "tv", "reason": "An intense action anime with complex characters and an engaging plot."},
            {"title": "Your Name", "type": "movie", "reason": "A beautiful anime romance with stunning visuals and emotional depth."}
        ],
        "Hollywood Movie Enthusiast": [
            {"title": "The Shawshank Redemption", "type": "movie", "reason": "A classic drama about hope and perseverance with excellent performances."},
            {"title": "Inception", "type": "movie", "reason": "A mind-bending thriller with stunning visuals and an intricate plot."},
            {"title": "The Dark Knight", "type": "movie", "reason": "An exceptional superhero film with outstanding performances and direction."}
        ],
        "Bollywood Fan": [
            {"title": "3 Idiots", "type": "movie", "reason": "A heartwarming story about friendship, education, and following your passion."},
            {"title": "Dangal", "type": "movie", "reason": "An inspiring sports drama based on a true story with exceptional performances."},
            {"title": "Lagaan", "type": "movie", "reason": "A classic period drama that combines sports, romance, and social commentary."}
        ],
        "K-Drama Lover": [
            {"title": "Crash Landing on You", "type": "tv", "reason": "A romantic drama with political elements and charming performances."},
            {"title": "Squid Game", "type": "tv", "reason": "A thrilling survival drama with social commentary and unexpected twists."},
            {"title": "Goblin", "type": "tv", "reason": "A fantasy romance with emotional depth and supernatural elements."}
        ],
        "TV Series Binger": [
            {"title": "Breaking Bad", "type": "tv", "reason": "A gripping drama about a chemistry teacher turned drug manufacturer."},
            {"title": "Stranger Things", "type": "tv", "reason": "A nostalgic series with supernatural elements and compelling characters."},
            {"title": "The Crown", "type": "tv", "reason": "A historical drama about the British royal family with excellent performances."}
        ],
        "Indie Film Appreciator": [
            {"title": "Parasite", "type": "movie", "reason": "A thought-provoking social commentary with unexpected twists and excellent direction."},
            {"title": "Moonlight", "type": "movie", "reason": "A beautiful coming-of-age story with excellent performances and direction."},
            {"title": "Lady Bird", "type": "movie", "reason": "A heartfelt coming-of-age story with authentic characters and relationships."}
        ]
    }
    
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
        st.session_state.debug_info = "Attempting to get recommendations from Gemini API..."
        response = ask_gemini(prompt)
        st.session_state.debug_info = f"Gemini API response received: {response[:100]}..."
        
        parsed_response = json.loads(response)
        st.session_state.debug_info = "Successfully parsed JSON response for recommendations"
        
        # Verify the structure is correct
        if (isinstance(parsed_response, list) and 
            all('title' in r and 'type' in r and 'reason' in r for r in parsed_response) and
            len(parsed_response) >= 1):
            return parsed_response
        else:
            st.session_state.debug_info = "Response had incorrect structure, using fallback recommendations"
            return default_recommendations.get(persona, default_recommendations["Hollywood Movie Enthusiast"])
            
    except Exception as e:
        st.session_state.debug_info = f"Error in get_recommendations: {str(e)}"
        st.error(f"Error generating recommendations: {e}")
        return default_recommendations.get(persona, default_recommendations["Hollywood Movie Enthusiast"])

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
    # Check API keys first and show warnings if missing
    if TMDB_API_KEY == "missing" or GEMINI_API_KEY == "missing":
        st.warning("""
        ⚠️ **API Keys Missing** ⚠️
        
        One or more API keys are missing. The app will work with sample data, but for the full experience:
        
        1. Get a TMDB API key from: https://www.themoviedb.org/settings/api
        2. Get a Gemini API key from: https://aistudio.google.com/app/apikey
        3. Update the `.streamlit/secrets.toml` file with your keys
        """)
    
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
                st.session_state.debug_info = f"Selected persona: {persona}, moving to generating_questions"
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
    
    # Debug info
    st.write(f"Generating questions for persona: {st.session_state.persona}")
    
    # Generate questions
    questions = generate_questions(st.session_state.persona)
    
    if questions:
        st.session_state.questions = questions
        st.session_state.step = 'asking_questions'
        st.write("Questions generated successfully, moving to asking_questions")
    else:
        # If we failed to generate questions, we'll try a total of 3 times before giving up
        if st.session_state.retry_count < 3:
            st.session_state.retry_count += 1
            st.write(f"Retry attempt {st.session_state.retry_count}...")
            # Short delay before retry
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to generate questions after multiple attempts. Please try again.")
            st.session_state.step = 'welcome'
            st.session_state.retry_count = 0
    
    # Show debug info
    if 'debug_info' in st.session_state:
        st.write(f"Debug info: {st.session_state.debug_info}")
    
    st.rerun()

# Display current question and options
def show_question():
    current_q = st.session_state.current_question
    
    # Debug information
    st.write(f"Current question index: {current_q}")
    st.write(f"Total questions: {len(st.session_state.questions)}")
    
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
        
        # Use unique keys for each option button to avoid conflicts
        for i, option in enumerate(question['options']):
            if st.button(option, key=f"q{current_q}_option_{i}", use_container_width=True):
                st.write(f"Selected: {option}")
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
    
    # Debug information
    st.write(f"Generating recommendations for persona: {st.session_state.persona}")
    st.write(f"Based on {len(st.session_state.answers)} answers")
    
    # Fallback recommendations if the AI fails
    fallback_recommendations = [
        {
            "title": "The Matrix",
            "type": "movie",
            "reason": "A sci-fi classic that combines action, philosophy, and groundbreaking visuals."
        },
        {
            "title": "Stranger Things",
            "type": "tv",
            "reason": "A nostalgic series with supernatural elements and compelling characters."
        },
        {
            "title": "Inception",
            "type": "movie",
            "reason": "A mind-bending thriller with stunning visuals and an intricate plot."
        }
    ]
    
    # Try to get AI recommendations, use fallbacks if it fails
    try:
        recommendations = get_recommendations(
            st.session_state.persona, 
            st.session_state.questions, 
            st.session_state.answers
        )
        
        if not recommendations or len(recommendations) == 0:
            st.write("Using fallback recommendations")
            recommendations = fallback_recommendations
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        recommendations = fallback_recommendations
    
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
    
    # Add debug controls
    with st.sidebar:
        st.write("Debug Panel")
        st.write(f"Current step: {st.session_state.step}")
        if st.button("Reset App"):
            st.session_state.clear()
            st.rerun()
    
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
    
    # Show debug info at the bottom for development
    if st.checkbox("Show Debug Info"):
        st.write("Debug Information:")
        for key, value in st.session_state.items():
            st.write(f"{key}: {value}")

if __name__ == "__main__":
    main()

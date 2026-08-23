import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import random
import string
from datetime import datetime
import base64
import os
import re
import ast
import json
from supabase import create_client, Client

# Load all questions from the single JSON file
with open('data/questions.json', 'r', encoding='utf-8') as f:
    json_data = json.load(f)

# MAGIC TRICK: Assign the JSON data to the exact variable names your app already expects!
KARNAUHOVA_QUESTIONS = json_data.get("Karnauhova", {})
GLOBE_CULTURE_QUESTIONS = json_data.get("GLOBE_Culture", {})
GLOBE_LEADERSHIP_QUESTIONS = json_data.get("GLOBE_Leadership", {})
    
# Initialize Supabase client (cached so it doesn't reconnect on every click)
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase: Client = init_supabase()

def save_user_profile(anonymous_id, nationality, framework, scores, comparison_type, comparison_country=None):
    """Saves the user's test results to the Supabase database."""
    try:
        # Magic trick: Converts special calculation numbers into standard Python numbers for Supabase
        clean_scores = json.loads(json.dumps(scores))

        data = {
            "anonymous_id": str(anonymous_id),
            "nationality": str(nationality),
            "test_type": str(framework),
            "scores": clean_scores,
            "comparison_type": str(comparison_type),
            "comparison_country": str(comparison_country) if comparison_country else None
        }
        
        supabase.table("user_profiles").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving profile: {e}")
        return False

def load_all_user_profiles(anonymous_id):
    """Loads ALL saved profiles for a specific user ID."""
    try:
        response = supabase.table("user_profiles").select("*").eq("anonymous_id", anonymous_id).execute()
        return response.data # This returns a list of all matching rows
    except Exception as e:
        st.error(f"Error loading profiles: {e}")
        return []

def check_duplicate_profile(anonymous_id, framework, comparison_type, comparison_country):
    """Checks if a user already has a saved profile for this exact combination."""
    try:
        # Search for matching profiles
        response = supabase.table("user_profiles").select("id").eq("anonymous_id", anonymous_id).eq("test_type", str(framework)).eq("comparison_type", comparison_type).execute()
        
        # Check the results in Python to handle NULL countries safely
        for row in response.data:
            db_country = row.get('comparison_country')
            if db_country == comparison_country:
                return True # Found a match!
        return False
    except Exception as e:
        return False

def format_dimension_name(name):
    """Translates ugly backend names into pretty display names."""
    name = str(name)
    pretty_names = {
        "TimeFocus": "Time Focus",
        "TimeOrientation": "Time Orientation",
        "PerformanceOrientation": "Performance Orientation",
        "FutureOrientation": "Future Orientation",
        "HumaneOrientation": "Humane Orientation",
        "InstitutionalCollectivism": "Institutional Collectivism",
        "InGroupCollectivism": "In-group Collectivism",
        "GenderEgalitarianism": "Gender Egalitarianism",
        "PowerDistance": "Power Distance",
        "UncertaintyAvoidance": "Uncertainty Avoidance",
        "CharismaticValueBased": "Charisma",
        "TeamOriented": "Team Oriented",
        "HumaneOriented": "Humane Oriented",
        "SelfProtective": "Self-protective"
    }
    return pretty_names.get(name, name)

# Page configuration
st.set_page_config(
    page_title="CQ Compass - Cultural Intelligence Assessment",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for flexible theming
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* 1. MAIN BACKGROUND & TYPOGRAPHY */
.stApp {
    background-color: var(--bg-main) !important;
}

h1, h2, h3, h4, h5 {
    font-family: 'Playfair Display', serif !important;
    color: var(--text-main) !important;
}

p, li, span, label, div {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-main) !important;
}

/* 2. CARDS AND CONTAINERS */
.stMetric, .stAlert, .recommendation-card {
    background-color: var(--bg-secondary) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    color: var(--text-main) !important;
}

/* 3. BUTTONS */
.stButton > button {
    background-color: transparent !important;
    color: var(--text-main) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    border: 2px solid var(--text-secondary) !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background-color: rgba(59, 111, 160, 0.1) !important; /* Subtle accent glow */
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2) !important;
}

/* 4. PLOTLY CHART ICONS */
.modebar-btn path {
    fill: var(--text-secondary) !important;
}
.modebar-btn:hover path {
    fill: var(--accent) !important;
}
    
/* 5. SELECT BOXES AND INPUTS */
div[data-baseweb="select"] > div,
.stTextInput > div > div > input {
    background-color: var(--bg-secondary) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--text-secondary) !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div > div > div {
    color: var(--text-main) !important;
}

div[data-baseweb="select"] div[role="option"][aria-selected="true"] {
    color: var(--text-main) !important;
    background-color: var(--bg-main) !important;
}

/* 6. RADIO BUTTONS */
.stRadio > div {
    background-color: transparent !important;
}
.stRadio > div > label {
    color: var(--text-main) !important;
    padding: 8px !important;
    border-radius: 6px !important;
}

/* 7. PROGRESS BAR */
.stProgress > div > div > div > div {
    background-color: var(--accent) !important;
}

/* 8. RECOMMENDATION CARDS (Using Semantic Variables) */
.recommendation-card {
    background-color: var(--bg-secondary);
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
.recommendation-red {
    border-left: 4px solid var(--color-danger) !important;
}
.recommendation-yellow {
    border-left: 4px solid var(--color-warning) !important;
}
.recommendation-green {
    border-left: 4px solid var(--color-success) !important;
}

/* 9. ANONYMOUS ID DISPLAY */
.anonymous-id {
    background-color: var(--accent);
    color: var(--bg-main) !important; /* Ensures high contrast */
    padding: 15px 25px;
    border-radius: 8px;
    font-family: 'Inter', monospace;
    font-size: 1.2em;
    font-weight: 600;
    display: inline-block;
    margin: 10px 0;
}

/* 10. URGENCY BADGES */
.urgency-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 600;
    margin-bottom: 10px;
}
.urgency-red {
    background-color: var(--color-danger);
    color: #FFFFFF;
}
.urgency-yellow {
    background-color: var(--color-warning);
    color: #1B2838;
}
.urgency-green {
    background-color: var(--color-success);
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)

# Helper functions
def generate_anonymous_id():
    """Generate a random anonymous ID in format CQ-XXXX-XXX"""
    digits = ''.join(random.choices(string.digits, k=4))
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    return f"CQ-{digits}-{letters}"

def load_data(filename):
    """Load CSV data from the data folder"""
    filepath = os.path.join('data', filename)
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        st.error(f"File not found: {filepath}")
        return pd.DataFrame()

def load_user_profile(anonymous_id):
    """Loads a user's profile from the database using their anonymous ID."""
    try:
        # Query the database for a matching anonymous_id
        response = supabase.table("user_profiles").select("*").eq("anonymous_id", anonymous_id).execute()
        
        if response.data:
            return response.data[0]  # Return the first matching record
        return None
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        return None

def calculate_dimension_score(answers, questions_per_dimension):
    """Calculate average score for each dimension"""
    scores = {}
    for dim, answers_list in answers.items():
        if answers_list:
            scores[dim] = round(sum(answers_list) / len(answers_list), 1)
    return scores

def create_radar_chart(scores, labels, title="Cultural Profile"):
    """Create a radar/spider chart using Plotly"""
    # Apply the pretty names to the labels
    formatted_labels = [format_dimension_name(label) for label in labels]
    
    # Close the radar chart by repeating the first value
    values = list(scores.values()) + [list(scores.values())[0]]
    labels_closed = formatted_labels + [formatted_labels[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels_closed,
        fill='toself',
        name='Your Profile',
        line_color='#2E5C8A',
        fillcolor='rgba(59, 111, 160, 0.15)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 7],
                gridcolor='#E5E7EB',  # Light gray for subtle, elegant grid lines
                tickfont=dict(color='#1C2D4B', size=10) # Dark midnight blue text
            ),
            angularaxis=dict(
                gridcolor='#E5E7EB',  # Light gray grid lines
                tickfont=dict(color='#1C2D4B', size=11, family='Playfair Display') # Dark blue, elegant font
            ),
            bgcolor='rgba(0,0,0,0)' # Transparent! Blends perfectly into the white card
        ),
        showlegend=True,
        title=dict(
            text=title,
            font=dict(color='#1C2D4B', size=22, family='Playfair Display') # Dark blue title
        ),
        plot_bgcolor='rgba(0,0,0,0)', # Transparent plot area
        paper_bgcolor='rgba(0,0,0,0)', # Transparent paper area
        font=dict(color='#1C2D4B', family='Inter'), # Dark blue default text
        legend=dict(
            font=dict(color='#1C2D4B', size=12),
            bgcolor='rgba(0,0,0,0)' # Transparent legend background
        )
    )
    
    return fig

def get_qualitative_label(score, scale_type, dimension=""):
        """Convert numerical score to qualitative label"""
        # Define Karnauhova poles with brief explanations
        karnauhova_poles = {
            "Time Focus": ("Monochronic (Strict scheduling)", "Polychronic (Flexible flow)"),
            "Time Orientation": ("Past-oriented (Tradition)", "Future-oriented (Innovation)"),
            "Space": ("Private (Boundaries)", "Public (Openness)"),
            "Power": ("Egalitarian (Flat hierarchy)", "Hierarchical (Status-driven)"),
            "Structure": ("Individualist (Self-reliant)", "Collectivist (Group-focused)"),
            "Competition": ("Cooperative (Harmony)", "Competitive (Achievement)"),
            "Communication": ("Low-context (Direct)", "High-context (Indirect)"),
            "Action": ("Being-oriented (Relationships)", "Doing-oriented (Results)")
        }

        if scale_type == "karnauhova":  # 1-5 scale
            pole1, pole2 = karnauhova_poles.get(dimension, ("Pole 1", "Pole 2"))
            if score <= 1.7:
                return f"Strongly {pole1}"
            elif score <= 2.6:
                return f"Moderately {pole1}"
            elif score <= 3.4:
                return "Aligned"
            elif score <= 4.2:
                return f"Moderately {pole2}"
            else:
                return f"Strongly {pole2}"
        else:  # 1-7 scale (GLOBE)
            if score <= 2.2:
                return "Low"
            elif score <= 3.6:
                return "Moderately Low"
            elif score <= 4.4:
                return "Moderate"
            elif score <= 5.8:
                return "Moderately High"
            else:
                return "High"

# Initialize session state and generate a new ID for new sessions
if 'anonymous_id' not in st.session_state or st.session_state.anonymous_id is None:
    import random
    import string
    numbers = ''.join(random.choices(string.digits, k=4))
    letters = ''.join(random.choices(string.ascii_lowercase, k=3))
    st.session_state.anonymous_id = f"CQ-{numbers}-{letters}"
if 'nationality' not in st.session_state:
    st.session_state.nationality = None
if 'gender' not in st.session_state:
    st.session_state.gender = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'selected_tests' not in st.session_state:
    st.session_state.selected_tests = []
if 'test_answers' not in st.session_state:
    st.session_state.test_answers = {}
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'user_scores' not in st.session_state:
    st.session_state.user_scores = {}

# Define all test questions
# Note: GLOBE questions would follow the same structure but are omitted here for brevity
# In production, you would include all 18 GLOBE Culture questions and 12 GLOBE Leadership questions
# For now, we'll create placeholder questions

# Page functions
def page_welcome():
    logo_path = "assets/cqc-logo.png"
    logo_html = ""
    
    # The Base64 Magic Trick to make local images work in HTML
    try:
        with open(logo_path, "rb") as f:
            b64_img = base64.b64encode(f.read()).decode()
        # Change the 60px below to make the logo bigger or smaller!
        logo_html = f'<img src="data:image/png;base64,{b64_img}" style="height: 60px; width: auto; vertical-align: middle; margin-right: 15px;">'
    except FileNotFoundError:
        pass

    # --- 1. CENTERED HEADER SECTION ---
    st.markdown(f"<h1 style='text-align: center; color: #111827; font-size: 3rem; margin-bottom: 10px;'>{logo_html} CQ Compass</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #111827; font-size: 1.5rem; margin-bottom: 20px;'>Cultural Intelligence Assessment & Development Platform</h3>", unsafe_allow_html=True)
    
    # Subtitle - Centered and constrained width so it looks neat
    st.markdown("<p style='text-align: center; font-size: 1.1em; color: #FCF2E5; max-width: 800px; margin: 0 auto;'>Discover your cultural profile. Compare it with other cultures.<br>Navigate differences with confidence.</p>", unsafe_allow_html=True)
    
    # --- 2. SPACER (Separates header from selects) ---
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
   
    # --- 3. THE SELECTION BOXES ---
    col1, col2 = st.columns(2)

    with col1:
        nationality_display = st.selectbox(
            "Select your nationality",
            ["Select country/region", "Brazil", "China", "Egypt", "India", "Iran", "Japan", "Malaysia", "Nigeria", "Russia", "USA", "Anglo", "Confucian Asia", "Eastern Europe", "Germanic Europe", "Latin America", "Latin Europe", "Middle East", "Nordic Europe", "Southern Asia", "Sub-Saharan Africa"],
            key="nationality_select"
        )
        country_map = {
            "Brazil": "Brazil", "China": "China", "Egypt": "Egypt", "India": "India", 
            "Iran": "Iran", "Japan": "Japan", "Malaysia": "Malaysia", "Nigeria": "Nigeria", 
            "Russia": "Russia", "USA": "USA", "Anglo": "Anglo", "Confucian Asia": "ConfucianAsia", 
            "Eastern Europe": "EasternEurope", "Germanic Europe": "GermanicEurope", 
            "Latin America": "LatinAmerica", "Latin Europe": "LatinEurope", "Middle East": "MiddleEast", 
            "Nordic Europe": "NordicEurope", "Southern Asia": "SouthernAsia", "Sub-Saharan Africa": "SubSaharanAfrica"
        }
        nationality = country_map.get(nationality_display, None)

    with col2:
        gender = st.selectbox(
            "Select your gender",
            ["Select", "Female", "Male", "Prefer not to say"],
            key="gender_select"
        )

    # --- 4. SPACER (Keeps the good distance between selects and buttons) ---
    st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)

    # --- 5. THE BUTTONS ---
    c1, c2, c3, c4 = st.columns(4)

    with c2:
        if st.button("Returning User? Enter your code", use_container_width=True, key="returning_user_btn"):
            st.session_state.current_page = 7
            st.rerun()

    with c3:
        is_ready = (nationality is not None) and (gender != "Select")
        if st.button("Begin Assessment", use_container_width=True, disabled=not is_ready, key="begin_assessment_btn"):
            st.session_state.nationality = nationality
            st.session_state.current_page = 2
            st.rerun()
    
def page_test_selection():
    st.markdown("<h1 style='color: #EC5B38;'>Select Your Assessment</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Your Anonymous ID: <span class='anonymous-id'>{st.session_state.anonymous_id}</span></p>", unsafe_allow_html=True)
    st.markdown("<p style='color: #D4A843; font-size: 0.9em;'>⚠️ Save this ID to access your profile later. No email or password required.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Karnauhova Model")
        st.markdown("8 dimensions | 24 questions | ~12 minutes")
        st.markdown("Measures your personal cultural style across 8 key dimensions")
        karnauhova_selected = st.checkbox("Select", key="karnauhova_check")
    
    with col2:
        st.markdown("### GLOBE Cultural Practices")
        st.markdown("9 dimensions | 27 questions | ~14 minutes")
        st.markdown("Assesses your cultural practices based on the GLOBE framework")
        globe_culture_selected = st.checkbox("Select", key="globe_culture_check")
    
    with col3:
        st.markdown("### GLOBE Leadership Style")
        st.markdown("6 dimensions | 18 questions | ~9 minutes")
        st.markdown("Evaluates your personal leadership style and preferences")
        globe_leadership_selected = st.checkbox("Select", key="globe_leadership_check")
    
    selected_tests = []
    if karnauhova_selected:
        selected_tests.append("Karnauhova")
    if globe_culture_selected:
        selected_tests.append("GLOBE_Culture")
    if globe_leadership_selected:
        selected_tests.append("GLOBE_Leadership")
    
    st.session_state.selected_tests = selected_tests
    
    if st.button("Start Selected Test(s)", use_container_width=True, disabled=len(selected_tests) == 0):
        st.session_state.current_page = 3
        st.session_state.current_question = 0
        st.session_state.test_answers = {test: {} for test in selected_tests}
        st.rerun()

def page_test_administration():
# --- CSS TO TIGHTEN SPACING AND MATCH THEME ---
    st.markdown("""
    <style>
        /* 1. Fix the overlap: Pull the bar up just a little bit, not 50px! */
        .stProgress {
            margin-top: -10px !important;
            margin-bottom: -10px !important;
        }
        /* 2. Reduce space under the main title */
        h1 {
            margin-bottom: 5px !important;
            padding-bottom: 0px !important;
        }
        /* 3. Pull the "Question X of Y" text up closer to the bar */
        .stMarkdown p {
            margin-top: 0px !important;
            margin-bottom: 10px !important;
        }
        /* 4. BONUS: Force the Gold color using a stronger Streamlit selector! */
        div[data-testid="stProgress"] > div > div > div > div,
        .stProgress > div > div > div > div {
            background-color: #EC5B38 !important;
        }
    </style>
    """, unsafe_allow_html=True)    
    
    st.markdown("<h1 style='color: #EC5B38;'>Assessment in Progress</h1>", unsafe_allow_html=True)
    
    # Calculate total questions and current position
    total_questions = 0
    question_map = []
    
    for test_name in st.session_state.selected_tests:
        if test_name == "Karnauhova":
            questions = KARNAUHOVA_QUESTIONS
        elif test_name == "GLOBE_Culture":
            questions = GLOBE_CULTURE_QUESTIONS
        else:
            questions = GLOBE_LEADERSHIP_QUESTIONS
        
        for dimension, dim_questions in questions.items():
            for q_idx, question in enumerate(dim_questions):
                question_map.append({
                    "test": test_name,
                    "dimension": dimension,
                    "question": question,
                    "global_idx": total_questions
                })
                total_questions += 1
    
    current_idx = st.session_state.current_question
    current_item = question_map[current_idx]
    
    # --- CUSTOM PROGRESS BAR (Now using Master Palette Variables) ---
    progress_percent = int(((current_idx + 1) / total_questions) * 100)
    
    st.markdown(f"""
    <div style="
        background-color: var(--bg-secondary); 
        border: 1px solid var(--text-secondary); /* Adds a subtle outline so it's visible on light backgrounds */
        border-radius: 10px; 
        height: 20px; 
        width: 100%; 
        margin: 10px 0 20px 0;
        overflow: hidden;
    ">
        <div style="
            background-color: var(--accent); 
            height: 100%; 
            width: {progress_percent}%; 
            border-radius: 10px;
            transition: width 0.3s ease;
        ">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"<p style='text-align: center; color: var(--accent); margin-top: -10px; margin-bottom: 30px; font-weight: 500;'>Question {current_idx + 1} of {total_questions}</p>", unsafe_allow_html=True)

    # Display question
    pretty_name = format_dimension_name(current_item['dimension'])
    st.markdown(f"### {pretty_name}")
    st.markdown(f"**{current_item['question']['q']}**")
    
    # Display options
    current_answer = st.session_state.test_answers[current_item['test']].get(current_item['dimension'], [])
    
    # Find which question within this dimension we're on
    dim_questions = []
    if current_item['test'] == "Karnauhova":
        dim_questions = KARNAUHOVA_QUESTIONS[current_item['dimension']]
    elif current_item['test'] == "GLOBE_Culture":
        dim_questions = GLOBE_CULTURE_QUESTIONS[current_item['dimension']]
    else:
        dim_questions = GLOBE_LEADERSHIP_QUESTIONS[current_item['dimension']]
    
    q_in_dim_idx = dim_questions.index(current_item['question'])
    
    selected_option = st.radio(
        "Select your answer:",
        [opt[0] for opt in current_item['question']['options']],
        key=f"q_{current_idx}",
        index=None
    )
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Previous", use_container_width=True, disabled=current_idx == 0):
            st.session_state.current_question -= 1
            st.rerun()
    
    with col2:
        if selected_option:
            # Save answer
            score = [opt[1] for opt in current_item['question']['options'] if opt[0] == selected_option][0]
            
            if current_item['dimension'] not in st.session_state.test_answers[current_item['test']]:
                st.session_state.test_answers[current_item['test']][current_item['dimension']] = []
            
            # Update or add answer
            if len(st.session_state.test_answers[current_item['test']][current_item['dimension']]) > q_in_dim_idx:
                st.session_state.test_answers[current_item['test']][current_item['dimension']][q_in_dim_idx] = score
            else:
                st.session_state.test_answers[current_item['test']][current_item['dimension']].append(score)
            
            if current_idx < total_questions - 1:
                if st.button("Next →", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("Submit Assessment", use_container_width=True, type="primary"):
                    # Calculate scores
                    for test_name in st.session_state.selected_tests:
                        st.session_state.user_scores[test_name] = calculate_dimension_score(
                            st.session_state.test_answers[test_name],
                            0
                        )
                    
                    # Save to CSV
                    # save_user_profile()

                    st.session_state.current_page = 4
                    st.rerun()
    
def page_results():
    # Mandatory Nationality Check (Bypassed if user is loading a saved profile)
    if not st.session_state.get('nationality') and not st.session_state.get('returning_user'):
        st.warning("️ Please select your nationality on the Home page to see your results.")
        if st.button("Go back to Home"):
            st.session_state.current_page = 1
            st.rerun()
        return
        
    st.markdown("<h1 style='color: #EC5B38;'>Your Cultural Profile</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Anonymous ID: <span class='anonymous-id'>{st.session_state.anonymous_id}</span></p>", unsafe_allow_html=True)
    
    # Load country scores
    country_scores_df = load_data('country_scores.csv')

    # Display results for each test
    for test_name in st.session_state.selected_tests:
        st.markdown(f"## {test_name.replace('_', ' ')} Results")
        
        user_scores = st.session_state.user_scores[test_name]
        
        # Get national scores
        national_scores = {}
        for dimension in user_scores.keys():
            national_score = country_scores_df[
                (country_scores_df['Country'] == st.session_state.nationality) &
                (country_scores_df['Framework'] == test_name) &
                (country_scores_df['Dimension'] == dimension)
            ]['Score'].values
            
            if len(national_score) > 0:
                national_scores[dimension] = national_score[0]
            else:
                national_scores[dimension] = 3.5  # Default if not found
        
        # Create radar chart
        fig = go.Figure()
        
        # User scores
        user_values = list(user_scores.values()) + [list(user_scores.values())[0]]
        user_labels = list(user_scores.keys()) + [list(user_scores.keys())[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=user_values,
            theta=[format_dimension_name(l) for l in list(user_scores.keys()) + [list(user_scores.keys())[0]]],
            fill='toself',
            name='Your Profile',
            line_color='#2E5C8A',
            fillcolor='rgba(59, 111, 160, 0.15)'
        ))
        
        # National scores
        national_values = list(national_scores.values()) + [list(national_scores.values())[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=national_values,
            theta=[format_dimension_name(l) for l in user_labels],
            fill='toself',
            name=f'{(st.session_state.nationality or "National").replace("LatinAmerica", "Latin America")} Average',
            line_color='#1C2D4B',
            fillcolor='rgba(28, 45, 75, 0.15)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[1, 7],
                    gridcolor='#E5E7EB',
                    tickfont=dict(color='#1C2D4B')
                ),
                angularaxis=dict(
                    gridcolor='#E5E7EB',
                    tickfont=dict(color='#1C2D4B')
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#1C2D4B')
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.20,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1C2D4B", size=14)
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
        
        # Display score table
        st.markdown("### Detailed Scores")
        
        score_data = []
        for dimension, score in user_scores.items():
            scale_type = "karnauhova" if test_name == "Karnauhova" else "globe"
            label = get_qualitative_label(score, scale_type, dimension)
            score_data.append({
                "Dimension": format_dimension_name(dimension),
                "Your Score": score,
                "National/Regional Average": national_scores[dimension],
                "Your Personal Profile": label
            })
        
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)
        
        # Create 3 columns to put buttons side-by-side on desktop
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

        with nav_col2:
            if st.button("💾 Save Results", use_container_width=True, key="save_results_btn"):
                with st.spinner("Saving your profile to the database..."):
                    user_id = st.session_state.get("anonymous_id", "UNKNOWN")
                    user_nationality = st.session_state.get("nationality", "Unknown")
                    user_framework = st.session_state.get("selected_tests", "Unknown")
                    user_scores = st.session_state.get("user_scores", {})
                    
                    # Save as NATIONAL comparison
                    success = save_user_profile(
                        anonymous_id=user_id,
                        nationality=user_nationality,
                        framework=user_framework,
                        scores=user_scores,
                        comparison_type="National",
                        comparison_country=None
                    )
                    
                    if success:
                        st.session_state.profile_saved = True
                        st.success("Profile saved successfully!")
                        st.rerun() 

        with nav_col3:
            if st.button("Compare with Another Culture", use_container_width=True, key="btn_compare_from_profile"):
                st.session_state.current_page = 5 # Takes them to the Comparison page
                st.rerun()
    
    # Display Interpretations
    st.markdown("---") # Add a nice divider line
    st.markdown(f"<h3 style='color: var(--accent);'>Your Personal Interpretations</h3>", unsafe_allow_html=True)
    
    # 1. Load the interpretations CSV
    interpretations_df = load_data('interpretations.csv') 
    
    # 2. Loop through the user's scores to find the matching text
    for dimension, score in user_scores.items():
        # Find the row in the CSV that matches the Framework, Dimension, and Score Range
        mask = (
            (interpretations_df['Framework'] == test_name) & 
            (interpretations_df['Dimension'] == dimension) & 
            (score >= interpretations_df['Min_Score']) & 
            (score <= interpretations_df['Max_Score'])
        )
        
        # If we found a match, display it!
        if not interpretations_df.loc[mask].empty:
            interpretation_text = interpretations_df.loc[mask, 'Interpretation'].values[0]
            
            # Display as a beautiful card using CSS Variables
            st.markdown(f"""
            <div style="
                background-color: var(--bg-secondary); 
                border-left: 5px solid var(--accent); 
                padding: 20px; 
                border-radius: 8px; 
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                <h3 style="color: var(--text-main); margin-top: 0; margin-bottom: 10px; font-size: 1.5rem;">{format_dimension_name(dimension)}</h3>
                <p style="color: var(--text-main); margin: 0; font-size: 1.1rem; line-height: 1.6;">{interpretation_text}</p>
            </div>
            """, unsafe_allow_html=True)           
    
    #Add navigation at the bottom
    render_navigation()

def page_country_comparison():
    st.markdown("<h1 style='color: #EC5B38;'>Country Comparison</h1>", unsafe_allow_html=True)

    # 1. Always load the country data first
    country_scores_df = load_data('country_scores.csv')
    available_countries = country_scores_df['Country'].unique()
    available_countries = [c for c in available_countries if c != st.session_state.nationality]
    
    country_name_map = {
        "Brazil": "Brazil", "China": "China", "Egypt": "Egypt", "India": "India",
        "Iran": "Iran", "Japan": "Japan", "Malaysia": "Malaysia", "Nigeria": "Nigeria",
        "Russia": "Russia", "USA": "USA", "Anglo": "Anglo", "ConfucianAsia": "Confucian Asia",
        "EasternEurope": "Eastern Europe", "GermanicEurope": "Germanic Europe",
        "LatinAmerica": "Latin America", "LatinEurope": "Latin Europe", "MiddleEast": "Middle East",
        "NordicEurope": "Nordic Europe", "SouthernAsia": "Southern Asia", "SubSaharanAfrica": "Sub-Saharan Africa"
    }
    
    available_countries_pretty = [country_name_map.get(c, c) for c in available_countries]
    reverse_country_map = {v: k for k, v in country_name_map.items()}

    # 2. SMART RETURNING USER CHECK
    if st.session_state.get('comparison_country') and st.session_state.get('returning_user'):
        # We already know the country from the loaded profile! Skip the dropdown.
        target_country = st.session_state.comparison_country
        pretty_name = country_name_map.get(target_country, target_country)
        st.info(f"📂 Viewing saved comparison with **{pretty_name}**.")
        
        # Add a button to let them clear this and pick a new country if they want
        if st.button("Compare with a different country", key="clear_comparison_btn"):
            st.session_state.returning_user = False
            st.session_state.comparison_country = None
            st.rerun()
            
    else:
        # 3. NORMAL DROPDOWN CODE (Only shows if NOT a returning user)
        target_country_pretty = st.selectbox(
            "Select target country", 
            ["Select a country to compare..."] + available_countries_pretty
        )

        if target_country_pretty == "Select a country to compare...":
            st.info("👆 Please select a country from the dropdown above to see your comparison.")
            st.stop()
        
        # Reverse map the pretty name back to the raw CSV name
        target_country = reverse_country_map.get(target_country_pretty, target_country_pretty)

        st.session_state.comparison_country = target_country

    # 4. DRAWING THE CHARTS (Runs for BOTH returning users and new users!)
    if target_country:
        # Display comparison for each test
        for test_name in st.session_state.selected_tests:
            st.markdown(f"## {test_name.replace('_', ' ')} Comparison")
            
            user_scores = st.session_state.user_scores.get(test_name, {})
            
            # Get national and target scores
            national_scores = {}
            target_scores = {}
            
            for dimension in user_scores.keys():
                national_score = country_scores_df[
                    (country_scores_df['Country'] == st.session_state.nationality) &
                    (country_scores_df['Framework'] == test_name) &
                    (country_scores_df['Dimension'] == dimension)
                ]['Score'].values
                
                target_score = country_scores_df[
                    (country_scores_df['Country'] == target_country) &
                    (country_scores_df['Framework'] == test_name) &
                    (country_scores_df['Dimension'] == dimension)
                ]['Score'].values
                
                national_scores[dimension] = national_score[0] if len(national_score) > 0 else 3.5
                target_scores[dimension] = target_score[0] if len(target_score) > 0 else 3.5
            
            # Create 3-layer radar chart
            fig = go.Figure()
            
            labels = list(user_scores.keys())
            labels_closed = labels + [labels[0]]
            
            # User scores
            user_values = list(user_scores.values()) + [list(user_scores.values())[0]]
            fig.add_trace(go.Scatterpolar(
                r=user_values,
                theta=[format_dimension_name(l) for l in labels_closed],
                fill='toself',
                name='Your Profile',
                line_color='#2E5C8A',
                fillcolor='rgba(59, 111, 160, 0.15)'
            ))
            
            # National scores data preparation (Part 1)
            national_values = list(national_scores.values()) + [list(national_scores.values())[0]]
            
            # Initialize session state for the button if not exists
            if 'show_national_avg' not in st.session_state:
                st.session_state.show_national_avg = False

            # Add the trace to the chart IF the button is ON
            if st.session_state.show_national_avg:
                fig.add_trace(go.Scatterpolar(
                    r=national_values,
                    theta=[format_dimension_name(l) for l in labels_closed],
                    fill='toself',
                    name=f'{(st.session_state.nationality or "National").replace("LatinAmerica", "Latin America")} Average',
                    line_color='#1C2D4B',
                    fillcolor='rgba(28, 45, 75, 0.15)'
                ))

            # Target scores
            target_values = list(target_scores.values()) + [list(target_scores.values())[0]]
            fig.add_trace(go.Scatterpolar(
                r=target_values,
                theta=[format_dimension_name(l) for l in labels_closed],
                fill='toself',
                name=f'{target_country.replace("LatinAmerica", "Latin America")} Average',
                line_color='#A8906B',
                fillcolor='rgba(184, 165, 122, 0.15)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True, 
                        range=[1, 7],
                        gridcolor='#E5E7EB',
                        tickfont=dict(color='#1C2D4B')
                    ),
                    angularaxis=dict(
                        gridcolor='#E5E7EB',
                        tickfont=dict(color='#1C2D4B')
                    ),
                    bgcolor='rgba(0,0,0,0)'
                ),
                showlegend=True,
                legend=dict(
                     orientation="h", 
                     yanchor="bottom", 
                     y=1.20, 
                     xanchor="center", 
                     x=0.5, 
                     font=dict(color='#1C2D4B', size=12)
                 ),
                 plot_bgcolor='rgba(0,0,0,0)',
                 paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

# Move the CSS ABOVE the columns so it doesn't push the middle button down
            st.markdown("""
                <style>
                div[data-testid="stButton"] button[kind="secondary"] {
                    background-color: transparent !important;
                    color: #FFFFFF !important;
                    border: 1px solid #A8A492 !important;
                    border-radius: 6px !important;
                    padding: 8px 16px !important;
                    font-weight: 500 !important;
                    font-size: 14px !important;
                    transition: all 0.3s ease !important;
                }
                div[data-testid="stButton"] button[kind="secondary"]:hover {
                    background-color: rgba(59, 111, 160, 0.15) !important;
                    box-shadow: 0 0 10px rgba(59, 111, 160, 0.3) !important;
                }
                </style>
            """, unsafe_allow_html=True)

            # Create 3 columns for the action buttons
            col_match, col_toggle, col_save = st.columns(3)

            # 1. Closest Match Button (Placeholder)
            with col_match:
                if st.button("🎯 Closest Match", use_container_width=True, key="closest_match_btn"):
                    st.toast("Coming soon! This will show your best cultural fit.", icon="🎯")

            # 2. Show/Hide Toggle
            with col_toggle:
                if st.session_state.show_national_avg:
                    btn_text = "◉ Hide Home Country Average"
                else:
                    btn_text = "◎ Show Home Country Average"
                
                if st.button(btn_text, use_container_width=True, key="national_toggle_btn", type="secondary"):
                    st.session_state.show_national_avg = not st.session_state.show_national_avg
                    st.rerun()

            # 3. Save Results Button
            with col_save:
                if st.button("💾 Save Results", use_container_width=True, key="save_comparison_btn"):
                    with st.spinner("Saving your comparison to the database..."):
                        user_id = st.session_state.get("anonymous_id", "UNKNOWN")
                        user_nationality = st.session_state.get("nationality", "Unknown")
                        user_framework = str(st.session_state.get("selected_tests", "Unknown"))
                        user_scores = st.session_state.get("user_scores", {})
                        comparison_country = target_country 

                        # Save as SPECIFIC COUNTRY comparison
                        success = save_user_profile(
                            anonymous_id=user_id,
                            nationality=user_nationality,
                            framework=user_framework,
                            scores=user_scores,
                            comparison_type="Specific_Country",
                            comparison_country=comparison_country
                        )
                    
                        if success:
                            st.session_state.profile_saved = True
                            st.success("Comparison saved successfully!")
                            st.rerun()
                
                # Only show if it was just saved, then immediately clear the flag
                if st.session_state.get('profile_saved', False):
                    st.success("✅ Profile saved!")
                    st.caption(f"Your unique code: **{st.session_state.anonymous_id}**")
                    st.session_state.profile_saved = False
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown(f"### 🧭 Cultural Navigation Brief for {target_country}")

            if test_name == "Karnauhova":
                rec_df = load_data('dimension_recommendations_karnauhova.csv')
            elif test_name == "GLOBE_Culture":
                rec_df = load_data('dimension_recommendations_globe_culture.csv')
            else:
                rec_df = load_data('dimension_recommendations_globe_leadership.csv')

            user_scores = st.session_state.user_scores[test_name]
            recommendations = []

            for dimension, user_score in user_scores.items():
                target_score = country_scores_df[
                    (country_scores_df['Country'] == target_country) &
                    (country_scores_df['Framework'] == test_name) &
                    (country_scores_df['Dimension'] == dimension)
                ]['Score'].values

                if len(target_score) == 0: continue
                target_score = target_score[0]
                gap = abs(user_score - target_score)

                # 1. Determine Gap Category and Urgency
                if test_name == "Karnauhova":
                    if gap >= 2.0: gap_category, urgency = "High", "Red"
                    elif gap >= 1.0: gap_category, urgency = "Medium", "Yellow"
                    else: gap_category, urgency = "Low", "Green"
                else:
                    if gap >= 2.5: gap_category, urgency = "High", "Red"
                    elif gap >= 1.2: gap_category, urgency = "Medium", "Yellow"
                    else: gap_category, urgency = "Low", "Green"

                # 2. Determine Direction
                if user_score > target_score: direction = "UserHigher"
                elif user_score < target_score: direction = "UserLower"
                else: direction = "Aligned"

                # 3. Find the matching row in the CSV
                # FIX: If the gap is Low/Green, just look for the "Aligned" text regardless of direction
                if gap_category == "Low":
                    rec_row = rec_df[
                        (rec_df['Dimension'] == dimension) &
                        (rec_df['GapCategory'] == 'Low')
                    ]
                else:
                    rec_row = rec_df[
                        (rec_df['Dimension'] == dimension) &
                        (rec_df['GapCategory'] == gap_category) &
                        (rec_df['Direction'] == direction)
                    ]

                # 4. Append the recommendation
                if len(rec_row) > 0:
                    recommendations.append({
                        "dimension": dimension, 
                        "urgency": urgency, 
                        "gap_category": gap_category,
                        "text": rec_row.iloc[0]['RecommendationText'], 
                        "gap": gap
                    })
                else:
                    # Failsafe: If it STILL can't find it, print a warning to the console so we know
                    print(f"Warning: Missing recommendation for {dimension} ({gap_category}/{direction})")

            urgency_order = {"Red": 0, "Yellow": 1, "Green": 2}
            recommendations.sort(key=lambda x: (urgency_order[x['urgency']], -x['gap']))

            for rec in recommendations:
                urgency_class = f"recommendation-{rec['urgency'].lower()}"
                urgency_badge_class = f"urgency-{rec['urgency'].lower()}"
                badge_text = "🔴 Crucial" if rec['urgency'] == "Red" else "🟡 Important" if rec['urgency'] == "Yellow" else "🟢 Strength"

                st.markdown(f"""
                <div class="recommendation-card {urgency_class}">
                    <span class="urgency-badge {urgency_badge_class}">{badge_text}</span>
                    <h4 style='color: #EC5B38; margin-top: 10px;'>{format_dimension_name(rec['dimension'])}</h4>
                    <p style='color: #FCF2E5; line-height: 1.6;'>{rec['text']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

    # --- LOAD AND DISPLAY CULTURAL NOTES ---
    notes_file = 'data/cultural_notes.csv'

    # Check if the file exists to prevent crashes
    if os.path.exists(notes_file):
        df_notes = pd.read_csv(notes_file)
            
        # Check if a comparison country is currently selected in the session
        if st.session_state.get('comparison_country'):
            target_country = st.session_state.comparison_country
                
            # Filter the notes for the selected country
            country_notes = df_notes[df_notes['Country'] == target_country]
                
            # Display the notes if they exist
            if not country_notes.empty:
                st.markdown("### 💡 Cultural Context & Local Etiquette")
                st.caption(f"Key behavioral insights for interacting in {target_country.replace('LatinAmerica', 'Latin America')}.")
                    
                # Loop through each note and render the custom HTML card
                for index, row in country_notes.iterrows():
                    st.markdown(f"""
                    <div class="cultural-note-card">
                        <div class="note-category">{row['Category']}</div>
                        <div class="note-tip">{row['Tip']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    #Add navigation at the bottom
    render_navigation()
    
def page_gap_analysis():
    st.markdown(f"<h1 style='color: #EC5B38;'>Cultural Navigation Brief for {st.session_state.target_country}</h1>", unsafe_allow_html=True)
    
    target_country = st.session_state.target_country
    
    # Load data
    country_scores_df = load_data('country_scores.csv')
    
    for test_name in st.session_state.selected_tests:
        st.markdown(f"## {test_name.replace('_', ' ')} Gap Analysis")
        
        # Load recommendations
        if test_name == "Karnauhova":
            rec_df = load_data('dimension_recommendations_karnauhova.csv')
        elif test_name == "GLOBE_Culture":
            rec_df = load_data('dimension_recommendations_globe_culture.csv')
        else:
            rec_df = load_data('dimension_recommendations_globe_leadership.csv')
        
        user_scores = st.session_state.user_scores[test_name]
        
        recommendations = []
        
        for dimension, user_score in user_scores.items():
            # Get target country score
            target_score = country_scores_df[
                (country_scores_df['Country'] == target_country) &
                (country_scores_df['Framework'] == test_name) &
                (country_scores_df['Dimension'] == dimension)
            ]['Score'].values
            
            if len(target_score) == 0:
                continue
            
            target_score = target_score[0]
            
            # Calculate gap
            gap = abs(user_score - target_score)
            
            # Determine category and direction
            if test_name == "Karnauhova":
                if gap >= 2.0:
                    gap_category = "High"
                    urgency = "Red"
                elif gap >= 1.0:
                    gap_category = "Medium"
                    urgency = "Yellow"
                else:
                    gap_category = "Low"
                    urgency = "Green"
            else:  # GLOBE (1-7 scale)
                if gap >= 2.5:
                    gap_category = "High"
                    urgency = "Red"
                elif gap >= 1.2:
                    gap_category = "Medium"
                    urgency = "Yellow"
                else:
                    gap_category = "Low"
                    urgency = "Green"
            
            if user_score > target_score:
                direction = "UserHigher"
            elif user_score < target_score:
                direction = "UserLower"
            else:
                direction = "Aligned"
            
            # Get recommendation
            rec_row = rec_df[
                (rec_df['Dimension'] == dimension) &
                (rec_df['GapCategory'] == gap_category) &
                (rec_df['Direction'] == direction)
            ]

def page_profile_access():
    st.markdown("<h1 style='color: #EC5B38;'>Access Your Profile</h1>", unsafe_allow_html=True)
    
    anonymous_id = st.text_input("Enter your Anonymous ID", key="access_id_input")
    
    # 1. The "Find" Button
    if st.button("Find Profiles", use_container_width=True, key="find_profiles_btn"):
        if anonymous_id:
            profiles = load_all_user_profiles(anonymous_id.strip())
            if profiles:
                # Save the results to memory so we can use them after the refresh
                st.session_state.found_profiles = profiles
                st.session_state.show_profile_menu = True
                st.success(f"Found {len(profiles)} saved profile(s)!")
                st.rerun() # Refresh to show the menu cleanly
            else:
                st.warning("No profiles found for this ID. Please check the ID or take a new assessment.")
                st.session_state.show_profile_menu = False
        else:
            st.warning("Please enter an ID first.")

    # 2. The Menu and "Load" Button (Safely OUTSIDE the first button's block)
    if st.session_state.get('show_profile_menu') and st.session_state.get('found_profiles'):
        profiles = st.session_state.found_profiles
        
        # Create a clean list of options
        profile_options = {}
        for p in profiles:
            framework = p.get('test_type', 'Unknown Framework')
            comp_type = p.get('comparison_type', 'National')
            comp_country = p.get('comparison_country', '')
            
            if comp_type == 'Specific_Country' and comp_country:
                label = f"{framework} vs. {comp_country}"
            else:
                label = f"{framework} vs. National Average"
                
            profile_options[label] = p 
            
        # Show the dropdown
        selected_label = st.selectbox("Which profile would you like to view?", list(profile_options.keys()))
        
        # The "Load" Button
        if st.button("Load Selected Profile", use_container_width=True, key="load_selected_btn"):
            selected_profile = profile_options[selected_label]
            
            # Load data into session state
            st.session_state.anonymous_id = selected_profile['anonymous_id']
            
            # Force nationality to pass the guard clause
            db_nationality = selected_profile.get('nationality')
            st.session_state.nationality = db_nationality if db_nationality else "Unknown"
            
            st.session_state.user_scores = selected_profile['scores']
            
            # Restore test type
            raw_test_type = selected_profile['test_type']
            try:
                import ast
                st.session_state.selected_tests = ast.literal_eval(raw_test_type)
            except:
                st.session_state.selected_tests = [raw_test_type]
            
            # --- SMART NAVIGATION ---
            # THIS IS THE CRITICAL PART!
            comp_type = selected_profile.get('comparison_type', 'National')
            comp_country = selected_profile.get('comparison_country', '')
            
            if comp_type == 'Specific_Country' and comp_country:
                # If they saved a country comparison, send them to Page 5!
                st.session_state.current_page = 5
                st.session_state.comparison_country = comp_country # Tell Page 5 which country to use!
            else:
                # Otherwise, send them to the standard Personal Results (Page 4)
                st.session_state.current_page = 4
                
            st.session_state.returning_user = True
            
            st.rerun()
            
# --- NAVIGATION FUNCTION ---
def render_navigation():
    # --- GLOBAL BUTTON STYLING (Keep your existing CSS here if you have it) ---
    
    # Create 4 columns for the bottom navigation
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

    with nav_col1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home_btn"):
            st.session_state.current_page = 1
            st.rerun()

    with nav_col2:
        # FIX FOR Q2: Renamed from "Assessment" to "Take a test"
        if st.button("📝 Take a test", use_container_width=True, key="nav_assess_btn"):
            st.session_state.current_page = 2
            st.rerun()

    with nav_col3:
        if st.button("🌍 Compare", use_container_width=True, key="nav_compare_btn"):
            st.session_state.current_page = 5
            st.rerun()

    with nav_col4:
        # FIX FOR Q1: Routes to Page 7 (Access Your Profile)
        # Note: We use "nav_profile_btn" as the key to avoid the crash we had earlier!
        if st.button("📊 Profile", use_container_width=True, key="nav_profile_btn"):
            st.session_state.current_page = 7
            st.session_state.returning_user = False # Reset flags so the ID input box appears
            st.rerun()

# Main app logic
def main():
    # --- MASTER COLOR PALETTE & GLOBAL STYLES ---
    st.markdown("""
    <style>
        /* 1. DEFINE THE PALETTE (Change these 5 hex codes to change the whole app!) */
        :root {
            /* 1. MAIN UI COLORS (Change these to test new palettes!) */
            --bg-main: #F9F7F5;          /* General Background */
            --bg-secondary: #FFFFFF;     /* Cards, Inputs, Dropdowns */
            --text-main: #1C2D4B;        /* Primary Text */
            --text-secondary: #A8906B;   /* Borders, Subtle Text, Icons */
            --accent: #2E5C8A;           /* Buttons Hover, Progress Bar, Highlights */
            
            /* 2. SEMANTIC COLORS (For alerts, badges, and recommendations) */
            --color-danger: #C75B3A;     /* Red / Urgent */
            --color-warning: #D4A843;    /* Yellow / Caution */
            --color-success: #7A9E7E;    /* Green / Aligned */
        }

        /* 2. GENERAL BACKGROUND & PRIMARY TEXT */
        .stApp {
            background-color: var(--bg-main) !important;
            color: var(--text-main) !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* 3. BUTTONS (Background, Border, and Hover) */
        div[data-testid="stButton"] button {
            background-color: transparent !important;
            border: 2px solid var(--text-secondary) !important;
            color: var(--text-main) !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stButton"] button:hover {
            border-color: var(--accent) !important;
            color: var(--accent) !important;
            background-color: rgba(59, 111, 161, 0.1) !important;
        }

        /* 6. SELECTION FIELDS (Dropdowns, Text Inputs) */
        .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
            background-color: var(--bg-secondary) !important;
            color: var(--text-main) !important;
            border: 1px solid var(--text-secondary) !important;
        }

        /* 5. PROGRESS BAR (For your custom HTML progress bar) */
        .custom-progress-bg { background-color: var(--bg-secondary) !important; }
        .custom-progress-fill { background-color: var(--accent) !important; 
        }

        /* --- CULTURAL NOTES CARDS --- */
        .cultural-note-card {
            background-color: var(--bg-secondary);
            border-left: 4px solid var(--text-secondary);
            padding: 16px 20px;
            margin-bottom: 16px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .note-category {
            color: var(--text-main);
            font-weight: 700;
            font-size: 1.1em;
            margin-bottom: 6px;
            font-family: 'Inter', sans-serif;
        }

        .note-tip {
            color: var(--text-main);
            font-size: 1em;
            line-height: 1.5;
            font-family: 'Inter', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- YOUR EXISTING PAGE ROUTING ---
    if st.session_state.current_page == 1:
        page_welcome()
    elif st.session_state.current_page == 2:
        page_test_selection()
    elif st.session_state.current_page == 3:
        page_test_administration()
    elif st.session_state.current_page == 4:
        page_results()
    elif st.session_state.current_page == 5:
        page_country_comparison()
    elif st.session_state.current_page == 6:
        page_gap_analysis()
    elif st.session_state.current_page == 7:
        page_profile_access()

if __name__ == "__main__":
    main()

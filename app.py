import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import random
import string
from datetime import datetime
import os
import re
from supabase import create_client, Client

# Initialize Supabase client (cached so it doesn't reconnect on every click)
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase: Client = init_supabase()

def save_user_profile(anonymous_id, nationality, test_type, scores_dict):
    """Saves the user's test results to the Supabase database."""
    try:
        data = {
            "anonymous_id": anonymous_id,
            "nationality": nationality,
            "test_type": test_type,
            "scores": scores_dict
        }
        supabase.table("user_profiles").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving profile: {e}")
        return False
        
def load_user_profile(anonymous_id):
    """Loads a user's profile from the database using their anonymous ID."""
    try:
        response = supabase.table("user_profiles").select("*").eq("anonymous_id", anonymous_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        return None

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

# Custom CSS for dark academia theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* Main background */
.stApp {
    background-color: #1B2838;
}

/* Typography */
h1, h2, h3, h4, h5 {
    font-family: 'Playfair Display', serif !important;
    color: #F5F0E8 !important;
}

p, li, span, label {
    font-family: 'Inter', sans-serif !important;
    color: #F5F0E8 !important;
}

/* Cards and containers */
.stMetric, .stAlert {
    background-color: #243447 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
}

/* Buttons */
.stButton > button {
    background-color: #C9A96E !important;
    color: #1B2838 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    border: none !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background-color: #D4B87A !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(201, 169, 110, 0.3) !important;
}

/* Darken Plotly chart icons */
    .modebar-btn path {
        fill: #C9A96E !important;
    }
    .modebar-btn:hover path {
        fill: #D4B87A !important;
    }
    
/* Select boxes and inputs - Fixed for visibility */
        div[data-baseweb="select"] > div {
            background-color: #243447 !important;
            border: 1px solid #3A4A5C !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] > div > div > div {
            color: #F5F0E8 !important;
        }

        div[data-baseweb="select"] div[role="option"][aria-selected="true"] {
        color: #F5F0E8 !important;
        }
        .stTextInput > div > div > input {
            background-color: #243447 !important;
            color: #F5F0E8 !important;
            border: 1px solid #3A4A5C !important;
            border-radius: 8px !important;
        }

/* Radio buttons */
.stRadio > div {
    background-color: transparent !important;
}

.stRadio > div > label {
    color: #F5F0E8 !important;
    padding: 8px !important;
    border-radius: 6px !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background-color: #C9A96E !important;
}

/* Recommendation cards */
.recommendation-card {
    background-color: #243447;
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.recommendation-red {
    border-left: 4px solid #C75B3A;
}

.recommendation-yellow {
    border-left: 4px solid #D4A843;
}

.recommendation-green {
    border-left: 4px solid #7A9E7E;
}

/* Anonymous ID display */
.anonymous-id {
    background-color: #C9A96E;
    color: #1B2838;
    padding: 15px 25px;
    border-radius: 8px;
    font-family: 'Inter', monospace;
    font-size: 1.2em;
    font-weight: 600;
    display: inline-block;
    margin: 10px 0;
}

/* Urgency badges */
.urgency-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 600;
    margin-bottom: 10px;
}

.urgency-red {
    background-color: #C75B3A;
    color: #F5F0E8;
}

.urgency-yellow {
    background-color: #D4A843;
    color: #1B2838;
}

.urgency-green {
    background-color: #7A9E7E;
    color: #F5F0E8;
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

def save_user_profile(anonymous_id, nationality, test_type, scores_dict):
    """Saves the user's test results to the Supabase database."""
    try:
        data = {
            "anonymous_id": anonymous_id,
            "nationality": nationality,
            "test_type": test_type,
            "scores": scores_dict  # This maps to the 'jsonb' column we created
        }
        # Insert the data into the 'user_profiles' table
        supabase.table("user_profiles").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error saving profile: {e}")
        return False

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
        line_color='#C9A96E',
        fillcolor='rgba(201, 169, 110, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 7],
                gridcolor='#3A4A5C',
                tickfont=dict(color='#F5F0E8')
            ),
            angularaxis=dict(
                gridcolor='#3A4A5C',
                tickfont=dict(color='#F5F0E8', size=10)
            ),
            bgcolor='#243447'
        ),
        showlegend=True,
        title=dict(
            text=title,
            font=dict(color='#F5F0E8', size=20, family='Playfair Display')
        ),
        plot_bgcolor='#1B2838',
        paper_bgcolor='#1B2838',
        font=dict(color='#F5F0E8')
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
KARNAUHOVA_QUESTIONS = {
    "TimeFocus": [
        {"q": "You are leading a project meeting with an international team. The agenda has 5 items, but the first topic sparks a rich, unexpected discussion. The scheduled time has passed. What do you do?",
         "options": [
             ("Politely interrupt and move to the next agenda item. The schedule must be respected.", 1),
             ("Allow 2-3 extra minutes, then firmly redirect the group back to the agenda.", 2),
             ("Quickly assess whether the discussion is more valuable than remaining items and adjust accordingly.", 3),
             ("Let the discussion continue and drop the least important agenda item to compensate.", 4),
             ("Fully embrace the organic flow. The best outcomes come from following the energy of the group.", 5)
         ]},
        {"q": "A colleague calls during your focused work time for a non-urgent matter. How do you respond?",
         "options": [
             ("I don't answer. I have blocked this time for deep work and will call back during open hours.", 1),
             ("I answer briefly, explain I'm busy, and schedule a specific time to talk later.", 2),
             ("I answer and spend a few minutes helping, then gently wrap up.", 3),
             ("I take the call and help as long as needed. Relationships come first.", 4),
             ("I'm happy to help. Interruptions are a natural part of the workday.", 5)
         ]},
        {"q": "You are organizing a social event for an international group. How do you structure the evening?",
         "options": [
             ("A detailed timeline: 7:00 arrivals, 7:30 dinner, 8:30 speeches, 9:30 networking, 10:30 close.", 1),
             ("A loose framework with approximate start times but some flexibility built in.", 2),
             ("A general plan (dinner, then socializing) but I let the evening unfold naturally.", 3),
             ("Minimal structure. I provide food, drinks, and a space, and trust the group.", 4),
             ("No schedule at all. People arrive when they arrive, eat when hungry, leave when ready.", 5)
         ]}
    ],
    "TimeOrientation": [
        {"q": "Your organization is considering a major strategic change. What type of argument do you find most persuasive?",
         "options": [
             ("This approach has been tested for decades and has a proven track record.", 1),
             ("This builds on established traditions while making careful, incremental improvements.", 2),
             ("This respects our history but also positions us for emerging trends.", 3),
             ("This is innovative and will give us a competitive advantage in the next 5 years.", 4),
             ("This completely reimagines our model. We need to disrupt ourselves before someone else does.", 5)
         ]},
        {"q": "A diplomatic delegation is visiting your city. What do you prioritize in the welcome program?",
         "options": [
             ("Historical monuments, museums, and sites showcasing our rich heritage.", 1),
             ("A mix of historical sites and meetings with established institutions.", 2),
             ("A Aligned program honoring past achievements while showcasing current developments.", 3),
             ("Tours of innovation hubs, tech parks, and startups showing where our country is heading.", 4),
             ("Presentations on future megaprojects and emerging industries that don't exist yet.", 5)
         ]},
        {"q": "When making an important personal decision (e.g., relocating), what weighs most heavily?",
         "options": [
             ("How this honors my family's history, roots, and previous generations' sacrifices.", 1),
             ("Whether this is consistent with values and lessons from my past experiences.", 2),
             ("A balance between honoring where I come from and creating new opportunities.", 3),
             ("How this positions me for growth and success in the coming years.", 4),
             ("The long-term vision of the life I want to build 10-20 years from now.", 5)
         ]}
    ],
    "Space": [
        {"q": "You are working in a shared office with international colleagues. How do you feel about the workspace?",
         "options": [
             ("I need a closed door and clear boundaries. My workspace is my personal territory.", 1),
             ("I prefer a quiet corner or partitioned desk with some visual and acoustic privacy.", 2),
             ("I'm comfortable in open-plan if private meeting rooms are available when needed.", 3),
             ("I enjoy open, shared spaces where I can interact with colleagues throughout the day.", 4),
             ("I thrive in bustling, communal environments. The more people around, the more energized.", 5)
         ]},
        {"q": "A new colleague asks a personal question (salary, marital status) during work lunch. How do you react?",
         "options": [
             ("Very uncomfortable. This is private and has no place in a professional setting.", 1),
             ("I give a vague, polite answer and steer back to work topics.", 2),
             ("I share a little to be friendly but keep most details to myself.", 3),
             ("I'm open to sharing. Knowing each other personally builds stronger professional trust.", 4),
             ("I welcome it enthusiastically. There is no separation between personal and professional life.", 5)
         ]},
        {"q": "When hosting an international business dinner, how do you handle seating?",
         "options": [
             ("Assigned seats with clear place cards. Each person has their designated space.", 1),
             ("Assigned seats for key guests, some flexibility for others.", 2),
             ("General seating plan (this table for delegation, that for our team) but no specific seats.", 3),
             ("Open seating. I encourage people to mix and sit wherever comfortable.", 4),
             ("No seating plan. Everyone shares food family-style and moves around freely.", 5)
         ]}
    ],
    "Power": [
        {"q": "During a negotiation, the most senior person on your team makes a statement with a factual error. What do you do?",
         "options": [
             ("I correct the error immediately and openly. Accuracy matters more than rank.", 1),
             ("I raise my hand: 'If I may add a clarification...' in a respectful but direct tone.", 2),
             ("I wait for a natural pause and gently reframe without explicitly calling it an error.", 3),
             ("I say nothing during the meeting but send a private message afterward.", 4),
             ("I would never contradict a senior leader in front of others. Their authority must be preserved.", 5)
         ]},
        {"q": "You are at a formal diplomatic reception. How do you approach greeting protocol?",
         "options": [
             ("I greet everyone equally with a handshake and first names, regardless of title.", 1),
             ("I use titles for the most senior but am more casual with junior staff.", 2),
             ("I follow my host's lead. If formal, I match; if casual, I match.", 3),
             ("I research the hierarchy beforehand and greet the most senior person first with formalities.", 4),
             ("I strictly observe all protocol: bowing, waiting to be introduced, full titles, deferring throughout.", 5)
         ]},
        {"q": "In a cross-cultural team project, how should decisions be made?",
         "options": [
             ("Every member has an equal vote regardless of position. The best idea wins.", 1),
             ("Everyone shares opinions, but the team lead makes the final call.", 2),
             ("The team discusses openly; the most experienced members naturally guide toward consensus.", 3),
             ("The senior leader consults a small inner circle, then announces the decision.", 4),
             ("The most senior person decides. Their authority makes them best suited to lead.", 5)
         ]}
    ],
    "Structure": [
        {"q": "Your company offers you a prestigious individual award, but your team contributed significantly. How do you handle it?",
         "options": [
             ("I accept proudly. I earned it through individual effort and initiative.", 1),
             ("I accept but publicly acknowledge my team's contributions in my speech.", 2),
             ("I feel uncomfortable accepting alone and suggest sharing with the team.", 3),
             ("I redirect recognition to the team. Group success matters more than individual achievement.", 4),
             ("I decline the individual award and insist it go to the entire team.", 5)
         ]},
        {"q": "You are assigned to a long-term project abroad. What is your primary relationship-building goal?",
         "options": [
             ("To expand my personal professional network and advance my individual career.", 1),
             ("To build a few strong professional connections for mutual future benefit.", 2),
             ("To integrate into the local community while maintaining independence and personal goals.", 3),
             ("To become a trusted group member, prioritizing their needs alongside my own.", 4),
             ("To fully immerse in the group's identity. My success is inseparable from the community's.", 5)
         ]},
        {"q": "When facing a major life decision, whose opinion matters most?",
         "options": [
             ("My own. I trust my individual judgment above all else.", 1),
             ("My own, but I value input from a close friend or mentor.", 2),
             ("A balance between personal desires and family/close circle expectations.", 3),
             ("My family and close community. Their well-being and approval are central.", 4),
             ("The collective. I would not decide without full consensus from family and community.", 5)
         ]}
    ],
    "Competition": [
        {"q": "In a business pitch competition, another team struggles with their technology. What do you do?",
         "options": [
             ("I focus on my own preparation. We are competitors; it's not my responsibility.", 1),
             ("I wish them luck but don't intervene. Fair competition means managing your own challenges.", 2),
             ("I offer a quick suggestion if I know the solution, but don't go out of my way.", 3),
             ("I actively help them fix the issue. A good relationship matters more than winning.", 4),
             ("I share my equipment freely. The best outcome is when everyone presents their best work.", 5)
         ]},
        {"q": "Your company is setting performance targets. What approach do you advocate?",
         "options": [
             ("Individual targets with clear rankings and bonuses for top performers.", 1),
             ("Individual targets with some team-based incentives to balance drive with collaboration.", 2),
             ("A mix of individual and team goals with equal weight.", 3),
             ("Team-based targets where the group succeeds or fails together.", 4),
             ("Collective organizational goals only. Internal competition is destructive.", 5)
         ]},
        {"q": "In a cross-cultural workshop, which group exercise format do you prefer?",
         "options": [
             ("A competitive debate where teams argue opposing positions and a winner is declared.", 1),
             ("Structured exercise with scoring, but teams can learn from each other.", 2),
             ("Collaborative problem-solving where all groups work on the same challenge and share results.", 3),
             ("A cooperative simulation where all participants work together for a single shared outcome.", 4),
             ("A community-building circle focused on mutual understanding, not producing a result.", 5)
         ]}
    ],
    "Communication": [
        {"q": "You receive an email: 'Your proposal is interesting. We will think about it and get back to you when the time is right.' How do you interpret this?",
         "options": [
             ("They are genuinely interested and will contact me soon with specific feedback.", 1),
             ("They are leaning positive but need more time. I'll follow up in a week.", 2),
             ("I'm not sure. The message is ambiguous, so I'll wait and ask for clarification.", 3),
             ("This is likely a polite refusal. 'Interesting' and 'when the time is right' suggest they won't say no directly.", 4),
             ("This is clearly a 'no.' Direct rejection would be rude, so they signal refusal indirectly.", 5)
         ]},
        {"q": "You need to give negative feedback to a colleague about their presentation. How do you deliver it?",
         "options": [
             ("Directly: 'Your presentation had three major issues. Here they are...'", 1),
             ("Honestly but constructively: 'Good effort, but specific areas need improvement.'", 2),
             ("Carefully, balancing positive and negative so the message is clear but not harsh.", 3),
             ("Indirectly, by asking questions that guide them to identify issues themselves.", 4),
             ("Very subtly, through hints or a trusted third party. Direct criticism would damage the relationship.", 5)
         ]},
        {"q": "Your counterpart says 'yes' but their body language is hesitant. How do you proceed?",
         "options": [
             ("I take the 'yes' at face value and move forward with the agreement.", 1),
             ("I note the hesitation but proceed, planning to confirm details in writing later.", 2),
             ("I pause and ask: 'Are you comfortable with all aspects of this proposal?'", 3),
             ("I read the non-verbal cues as discomfort and suggest revisiting with more flexibility.", 4),
             ("The 'yes' is about harmony, not agreement. I slow down, rebuild rapport, and look for the real answer in what is NOT said.", 5)
         ]}
    ],
    "Action": [
        {"q": "You meet a new international contact at a conference. What do you want to know first?",
         "options": [
             ("What do they do? Job title, company, current projects.", 1),
             ("Their professional achievements and goals they're working toward.", 2),
             ("A mix of what they do professionally and who they are as a person.", 3),
             ("Where they're from, their family, what they enjoy outside work.", 4),
             ("Who they are at their core—values, philosophy, what gives them meaning.", 5)
         ]},
        {"q": "Your organization evaluates a partnership's success. What metric matters most?",
         "options": [
             ("Tangible results: revenue, contracts signed, deadlines met.", 1),
             ("Measurable outcomes combined with qualitative stakeholder feedback.", 2),
             ("A balance between deliverables and relationship quality built during the process.", 3),
             ("The depth of trust and mutual understanding established between partners.", 4),
             ("The long-term harmony and shared purpose that emerged, regardless of short-term deliverables.", 5)
         ]},
        {"q": "When introducing yourself to international professionals, how do you describe yourself?",
         "options": [
             ("I'm a [title] at [company]. I specialize in [field] and recently completed [achievement].", 1),
             ("I work in [field] and I'm passionate about [goal]. Currently focused on [project].", 2),
             ("I work in [field], but I'm also a [hobby/identity]. I believe in balancing professional and personal growth.", 3),
             ("I value deep connections and meaningful experiences. My relationships define me more than my title.", 4),
             ("I'm a [cultural identity] who believes in [philosophy]. My work is just one expression of who I am.", 5)
         ]}
    ]
}

# Note: GLOBE questions would follow the same structure but are omitted here for brevity
# In production, you would include all 18 GLOBE Culture questions and 12 GLOBE Leadership questions
# For now, we'll create placeholder questions

GLOBE_CULTURE_QUESTIONS = {
    "PerformanceOrientation": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "Assertiveness": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "FutureOrientation": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "HumaneOrientation": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "InstitutionalCollectivism": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "InGroupCollectivism": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "GenderEgalitarianism": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "PowerDistance": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "UncertaintyAvoidance": [
        {"q": "Placeholder GLOBE question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ]
}

GLOBE_LEADERSHIP_QUESTIONS = {
    "CharismaticValueBased": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "TeamOriented": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "Participative": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "HumaneOriented": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "Autonomous": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ],
    "SelfProtective": [
        {"q": "Placeholder GLOBE Leadership question 1", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]},
        {"q": "Placeholder GLOBE Leadership question 2", "options": [(f"Option {chr(65+i)}", i+1) for i in range(7)]}
    ]
}

# Page functions
def page_welcome():
    st.markdown("<h1 style='text-align: center; color: #C9A96E;'>🌍 CQ Compass</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #F5F0E8;'>Cultural Intelligence Assessment & Development Platform</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em; margin-top: 30px;'>Discover your cultural profile. Compare it with other cultures. Navigate differences with confidence.</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)

    with col1:
        nationality_display = st.selectbox(
            "Select your nationality",
            ["Select country/region", "Brazil", "China", "Egypt", "India", "Iran", "Japan", "Malaysia", "Nigeria", "Russia", "USA", "Anglo", "Confucian Asia", "Eastern Europe", "Germanic Europe", "Latin America", "Latin Europe", "Middle East", "Nordic Europe", "Southern Asia", "Sub-Saharan Africa"],
            key="nationality_select"
        )
        # Map the two-word display name to the one-word CSV name
        country_map = {
            "Brazil": "Brazil", 
            "China": "China", 
            "Egypt": "Egypt", 
            "India": "India", 
            "Iran": "Iran", 
            "Japan": "Japan", 
            "Malaysia": "Malaysia", 
            "Nigeria": "Nigeria", 
            "Russia": "Russia", 
            "USA": "USA", 
            "Anglo": "Anglo", 
            "Confucian Asia": "ConfucianAsia", 
            "Eastern Europe": "EasternEurope", 
            "Germanic Europe": "GermanicEurope", 
            "Latin America": "LatinAmerica", 
            "Latin Europe": "LatinEurope", 
            "Middle East": "MiddleEast", 
            "Nordic Europe": "NordicEurope", 
            "Southern Asia": "SouthernAsia", 
            "Sub-Saharan Africa": "SubSaharanAfrica"
        }
        nationality = country_map.get(nationality_display, None)

    with col2:
        gender = st.selectbox(
            "Select your gender",
            ["Select", "Female", "Male", "Prefer not to say"],
            key="gender_select"
        )

    st.markdown("---")
    
    # Check if placeholders are still selected
    is_ready = (nationality is not None) and (gender != "Select")

    st.markdown("---")

    # Create 4 columns to cluster buttons in the center
    c1, c2, c3, c4 = st.columns(4)

    with c2:
        if st.button("Returning User? Enter your code", use_container_width=True, key="returning_user_btn"):
            st.session_state.current_page = 7
            st.rerun()

    with c3:
        if st.button("Begin Assessment", use_container_width=True, disabled=not is_ready, key="begin_assessment_btn"):
            # SAVE THE NATIONALITY HERE!
            st.session_state.nationality = nationality
            
            st.session_state.current_page = 2
            st.rerun()

def page_test_selection():
    st.markdown("<h1 style='color: #C9A96E;'>Select Your Assessment</h1>", unsafe_allow_html=True)
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
        st.markdown("9 dimensions | 18 questions | ~10 minutes")
        st.markdown("Assesses your cultural practices based on the GLOBE framework")
        globe_culture_selected = st.checkbox("Select", key="globe_culture_check")
    
    with col3:
        st.markdown("### GLOBE Leadership Style")
        st.markdown("6 dimensions | 12 questions | ~8 minutes")
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
    st.markdown("<h1 style='color: #C9A96E;'>Assessment in Progress</h1>", unsafe_allow_html=True)
    
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
    
    # Progress bar
    progress = (current_idx + 1) / total_questions
    st.progress(progress)
    st.markdown(f"<p style='text-align: center; color: #C9A96E;'>Question {current_idx + 1} of {total_questions}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    # Mandatory Nationality Check
    if not st.session_state.get('nationality'):
        st.warning("⚠️ Please select your nationality on the Home page to see your results.")
        if st.button("Go back to Home"):
            st.session_state.current_page = 1
            st.rerun()
        return
        
    st.markdown("<h1 style='color: #C9A96E;'>Your Cultural Profile</h1>", unsafe_allow_html=True)
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
            line_color='#C9A96E',
            fillcolor='rgba(201, 169, 110, 0.3)'
        ))
        
        # National scores
        national_values = list(national_scores.values()) + [list(national_scores.values())[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=national_values,
            theta=[format_dimension_name(l) for l in user_labels],
            fill='toself',
            name=f'{(st.session_state.nationality or "National").replace("LatinAmerica", "Latin America")} Average',
            line_color='#7A9E7E',
            fillcolor='rgba(122, 158, 126, 0.2)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[1, 7]),
                bgcolor='#243447'
            ),
            showlegend=True,
            plot_bgcolor='#1B2838',
            paper_bgcolor='#1B2838'
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
                font=dict(color="#D4AF37", size=14)
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
            if st.button("Save Results", use_container_width=True, key="save_results_btn"):
                with st.spinner("Saving your profile to the database..."):
                    # These match your debug list perfectly!
                    user_id = st.session_state.get("anonymous_id", "UNKNOWN")
                    user_nationality = st.session_state.get("nationality", "Unknown")
                    user_test_type = str(st.session_state.get("selected_tests", "Unknown"))
                    user_scores = st.session_state.get("user_scores", {})
                    
                    # This calls the function we put at the top of the file
                    success = save_user_profile(user_id, user_nationality, user_test_type, user_scores)
                    
                    if success:
                        st.session_state.profile_saved = True
                        st.rerun() 

        with nav_col3:
            if st.button("Compare with Another Culture", use_container_width=True, key="btn_compare_from_profile"):
                st.session_state.current_page = 5 # Takes them to the Comparison page
                st.rerun()

    #Add navigation at the bottom
    render_navigation()

def page_country_comparison():
    st.markdown("<h1 style='color: #C9A96E;'>Compare with Another Culture</h1>", unsafe_allow_html=True)
    
    # Load country scores
    country_scores_df = load_data('country_scores.csv')
    available_countries = country_scores_df['Country'].unique()
    available_countries = [c for c in available_countries if c != st.session_state.nationality]
    
    # Map raw CSV names to pretty display names (ADD YOUR NEW COUNTRIES HERE!)
    country_name_map = {
        "Brazil": "Brazil",
        "China": "China",
        "Egypt": "Egypt",
        "India": "India",
        "Iran": "Iran",
        "Japan": "Japan",
        "Malaysia": "Malaysia",
        "Nigeria": "Nigeria",
        "Russia": "Russia",
        "USA": "USA",
        "Anglo": "Anglo",
        "ConfucianAsia": "Confucian Asia",
        "EasternEurope": "Eastern Europe",
        "GermanicEurope": "Germanic Europe",
        "LatinAmerica": "Latin America",
        "LatinEurope": "Latin Europe",
        "MiddleEast": "Middle East",
        "NordicEurope": "Nordic Europe",
        "SouthernAsia": "Southern Asia",
        "SubSaharanAfrica": "Sub-Saharan Africa"
        # Add any other countries you've added to the CSV here
    }
    
    # Create a list of pretty names for the dropdown
    available_countries_pretty = [country_name_map.get(c, c) for c in available_countries]
    
    target_country_pretty = st.selectbox(
        "Select target country", 
        ["Select a country to compare..."] + available_countries_pretty
    )

    if target_country_pretty == "Select a country to compare...":
        st.info("👆 Please select a country from the dropdown above to see your comparison.")
        st.stop()
    
    # Reverse map the pretty name back to the raw CSV name for data lookup
    reverse_country_map = {v: k for k, v in country_name_map.items()}
    target_country = reverse_country_map.get(target_country_pretty, target_country_pretty)

    if target_country:
        # Display comparison for each test
        for test_name in st.session_state.selected_tests:
            st.markdown(f"## {test_name.replace('_', ' ')} Comparison")
            
            user_scores = st.session_state.user_scores[test_name]
            
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
                line_color='#C9A96E',
                fillcolor='rgba(201, 169, 110, 0.3)'
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
                    line_color='#7A9E7E',
                    fillcolor='rgba(122, 158, 126, 0.2)'
                ))

            # Target scores
            target_values = list(target_scores.values()) + [list(target_scores.values())[0]]
            fig.add_trace(go.Scatterpolar(
                r=target_values,
                theta=[format_dimension_name(l) for l in labels_closed],
                fill='toself',
                name=f'{target_country.replace("LatinAmerica", "Latin America")} Average',
                line_color='#C75B3A',
                fillcolor='rgba(199, 91, 58, 0.2)'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[1, 7]),
                    bgcolor='#243447'
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.20, xanchor="center", x=0.5, font=dict(color='#C9A96E', size=12)),
                plot_bgcolor='#1B2838',
                paper_bgcolor='#1B2838'
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

# Move the CSS ABOVE the columns so it doesn't push the middle button down
            st.markdown("""
                <style>
                div[data-testid="stButton"] button[kind="secondary"] {
                    background-color: transparent !important;
                    color: #FFFFFF !important;
                    border: 1px solid #C9A96E !important;
                    border-radius: 6px !important;
                    padding: 8px 16px !important;
                    font-weight: 500 !important;
                    font-size: 14px !important;
                    transition: all 0.3s ease !important;
                }
                div[data-testid="stButton"] button[kind="secondary"]:hover {
                    background-color: rgba(201, 169, 110, 0.15) !important;
                    box-shadow: 0 0 10px rgba(201, 169, 110, 0.4) !important;
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
                if st.button("💾 Save Results", use_container_width=True, key="save_results_btn"):
                    with st.spinner("Saving your profile to the database..."):
                        # These match your debug list perfectly!
                        user_id = st.session_state.get("anonymous_id", "UNKNOWN")
                        user_nationality = st.session_state.get("nationality", "Unknown")
                        user_test_type = str(st.session_state.get("selected_tests", "Unknown"))
                        user_scores = st.session_state.get("user_scores", {})
                    
                        # This calls the function we put at the top of the file
                        success = save_user_profile(user_id, user_nationality, user_test_type, user_scores)
                    
                        if success:
                            st.session_state.profile_saved = True
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

                if test_name == "Karnauhova":
                    if gap >= 2.0: gap_category, urgency = "High", "Red"
                    elif gap >= 1.0: gap_category, urgency = "Medium", "Yellow"
                    else: gap_category, urgency = "Low", "Green"
                else:
                    if gap >= 2.5: gap_category, urgency = "High", "Red"
                    elif gap >= 1.2: gap_category, urgency = "Medium", "Yellow"
                    else: gap_category, urgency = "Low", "Green"

                if user_score > target_score: direction = "UserHigher"
                elif user_score < target_score: direction = "UserLower"
                else: direction = "Aligned"

                rec_row = rec_df[
                    (rec_df['Dimension'] == dimension) &
                    (rec_df['GapCategory'] == gap_category) &
                    (rec_df['Direction'] == direction)
                ]

                if len(rec_row) > 0:
                    recommendations.append({
                        "dimension": dimension, "urgency": urgency, "gap_category": gap_category,
                        "text": rec_row.iloc[0]['RecommendationText'], "gap": gap
                    })

                else:
                # Fallback for Strengths/Aligned dimensions
                    recommendations.append({
                        "dimension": dimension,
                        "urgency": "Green",
                        "gap_category": "Low",
                        "text": f"You are naturally aligned with {target_country} in this area. This is a core strength that will help you connect easily!",
                        "gap": gap
                    })

            urgency_order = {"Red": 0, "Yellow": 1, "Green": 2}
            recommendations.sort(key=lambda x: (urgency_order[x['urgency']], -x['gap']))

            for rec in recommendations:
                urgency_class = f"recommendation-{rec['urgency'].lower()}"
                urgency_badge_class = f"urgency-{rec['urgency'].lower()}"
                badge_text = "🔴 Crucial" if rec['urgency'] == "Red" else "🟡 Important" if rec['urgency'] == "Yellow" else "🟢 Strength"

                st.markdown(f"""
                <div class="recommendation-card {urgency_class}">
                    <span class="urgency-badge {urgency_badge_class}">{badge_text}</span>
                    <h4 style='color: #C9A96E; margin-top: 10px;'>{format_dimension_name(rec['dimension'])}</h4>
                    <p style='color: #F5F0E8; line-height: 1.6;'>{rec['text']}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            
    #Add navigation at the bottom
    render_navigation()
    
def page_gap_analysis():
    st.markdown(f"<h1 style='color: #C9A96E;'>Cultural Navigation Brief for {st.session_state.target_country}</h1>", unsafe_allow_html=True)
    
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
    st.markdown("<h1 style='color: #C9A96E;'>Access Your Profile</h1>", unsafe_allow_html=True)
    
    anonymous_id = st.text_input("Enter your Anonymous ID")
    
    # Create 4 columns to center the buttons
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)

    with p_col2:
        if st.button("Load Profile", use_container_width=True, key="load_profile_btn"):
            # Use the variable directly (it's already captured above)
            anonymous_id = anonymous_id.strip()
                
            # Debug line
            st.write(f"DEBUG: Searching for ID -> '{anonymous_id}'")
                
            # Load from Supabase
            profile = load_user_profile(anonymous_id)
                
            if profile:
                st.session_state.anonymous_id = profile['anonymous_id']
                st.session_state.nationality = profile['nationality']
                st.session_state.user_scores = profile['scores']
                    
                st.success("Profile loaded successfully!")
                st.rerun()
            else:
                st.warning("Profile not found. Please check your ID or take a new assessment.")
                
    with p_col3:
        if st.button("← Back to Home", use_container_width=True, key="back_home_profile_btn"):
            st.session_state.current_page = 1
            st.rerun()
            
# --- NAVIGATION FUNCTION ---
def render_navigation():
    """Creates a simple, reliable navigation bar at the bottom of the page."""
    st.markdown("---")  # Horizontal line above the nav
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.session_state.current_page = 1
            st.rerun()
    with col2:
        if st.button("📝 Assessment", use_container_width=True, key="nav_assess"):
            st.session_state.current_page = 2
            st.rerun()
    with col3:
        if st.button("📊 Profile", use_container_width=True, key="nav_profile"):
            st.session_state.current_page = 4
            st.rerun()
    with col4:
        if st.button("🌍 Compare", use_container_width=True, key="nav_compare"):
            st.session_state.current_page = 5
            st.rerun()

# Main app logic
def main():
    # --- GLOBAL BUTTON STYLING ---
    st.markdown("""
        <style>
        /* Target all standard buttons in the app */
        div[data-testid="stButton"] button {
            background-color: transparent !important;
            color: #F8F9FA !important; /* Very light grey/white text */
            border: 1px solid #C9A96E !important; /* Golden border */
            border-radius: 6px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            transition: all 0.3s ease !important;
        }
        
        /* Elegant hover effect */
        div[data-testid="stButton"] button:hover {
            background-color: rgba(201, 169, 110, 0.15) !important; /* Subtle gold glow */
            color: #C9A96E !important; /* Text turns gold on hover */
            box-shadow: 0 0 10px rgba(201, 169, 110, 0.3) !important;
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

import streamlit as st
import random
from pyfiglet import Figlet
from collections import defaultdict
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Tuple, Literal, Dict, Any
import time # Import time for the delay

# -----------------------------
# State Definition for LangGraph
# -----------------------------
class GameState(TypedDict):
    mode: Optional[Literal['number', 'word', 'exit']]
    number_range: Tuple[int, int]
    attempts: int
    games_played: int
    word_options: Optional[list[str]]
    asked_categories: list[str]
    current_guess: Optional[str]
    user_input: Optional[Literal['yes', 'no']]
    low: int
    high: int
    mid: Optional[int]
    game_start: bool
    step_output: Optional[str]
    next_node: Optional[str]
    game_over: bool
    word_list: Optional[list[str]] # For the new word game logic
    word_game_step: int # To track the step in the word game

def initialize_state() -> GameState:
    return {
        'mode': None,
        'number_range': (1, 50),
        'attempts': 0,
        'games_played': st.session_state.get('game', {}).get('games_played', 0),
        'word_options': list(word_categories.keys()),
        'asked_categories': [],
        'current_guess': None,
        'user_input': None,
        'low': 1,
        'high': 50,
        'mid': None,
        'game_start': False,
        'step_output': None,
        'next_node': 'number_game', # Default
        'game_over': False,
        'word_list': list(word_categories.keys()), # Initialize word list
        'word_game_step': 0
    }

# -----------------------------
# Word game data
# -----------------------------
word_categories = {
    "apple": ["food", "fruit"],
    "chair": ["furniture", "object"],
    "elephant": ["animal"],
    "guitar": ["instrument", "object"],
    "rocket": ["vehicle", "space"],
    "pencil": ["stationery", "object"],
    "pizza": ["food"],
    "tiger": ["animal"]
}

# Build category to words mapping
category_to_words = defaultdict(list)
for word, categories in word_categories.items():
    for category in categories:
        category_to_words[category].append(word)

all_categories = sorted({cat for tags in word_categories.values() for cat in tags})

# -----------------------------
# Number Game Logic (Direct in Streamlit)
# -----------------------------
def number_game(state: GameState) -> GameState:
    low, high = state["number_range"]
    response = st.session_state.pop("response", None)

    if low < high:
        mid = (low + high) // 2
        if response == "yes":
            state["number_range"] = (mid + 1, high)
        elif response == "no":
            state["number_range"] = (low, mid)
        state["attempts"] += 1

        if state["number_range"][0] == state["number_range"][1]:
            st.session_state["message"] = f"🎉 Your number is {state['number_range'][0]}!"
            state["number_range"] = (1, 50)
            state["attempts"] = 0
            state["game_over"] = True  # Mark game as over
            return state
        else:
            st.session_state["question"] = f"Is your number greater than {(state['number_range'][0] + state['number_range'][1]) // 2}?"
            return state
    return state

# -----------------------------
# Streamlit UI Functions (Modified)
# -----------------------------
def show_game_menu():
    st.subheader("Choose a Game:")
    choice = st.radio("Select game type:", ["Number Game", "Word Game", "Exit Game"])

    if st.button("Start Game"):
        if choice == "Number Game":
            st.session_state.game['mode'] = 'number'
        elif choice == "Word Game":
            st.session_state.game['mode'] = 'word'
        else:
            st.session_state.game['mode'] = 'exit'
        st.rerun()

def play_number_game():
    st.subheader("🔢 Number Guessing Game")
    if 'langraph_state' not in st.session_state or st.session_state.langraph_state.get('mode') != 'number':
        st.session_state['langraph_state'] = initialize_state()
        st.session_state['langraph_state']['mode'] = 'number'
        st.session_state["question"] = "Welcome to the Number Game! Think of a number between 1 and 50.\nIs your number greater than 25?"
        st.session_state["message"] = ""

    state = st.session_state['langraph_state']
    
    # Show success message if game is over (correct number found)
    if st.session_state.get("message", ""):
        st.success(st.session_state["message"])
        
        # Game over buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔄 Play Again"):
                st.session_state['langraph_state']['number_range'] = (1, 50)
                st.session_state['langraph_state']['attempts'] = 0
                st.session_state['langraph_state']['game_over'] = False
                st.session_state["question"] = "Welcome to the Number Game! Think of a number between 1 and 50.\nIs your number greater than 25?"
                st.session_state["message"] = ""
                st.rerun()
        with col2:
            if st.button("🧠 Try Word Game"):
                switch_to_game('word')
        with col3:
            if st.button("🏠 Back to Menu"):
                reset_to_main_menu()
        with col4:
            if st.button("🚪 Exit Game"):
                st.session_state.game['mode'] = 'exit'
                st.rerun()
        return

    question = st.session_state.get("question", "")
    if question:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        with col1:
            response = st.radio(question, ["Yes", "No"])
            if st.button("Submit Answer"):
                st.session_state["response"] = response.lower()
                st.session_state['langraph_state'] = number_game(st.session_state['langraph_state'])
                st.rerun()
        with col2:
            if st.button("Exit Game"):
                st.session_state.game['mode'] = 'exit'
                st.rerun()
        with col3:
            if st.button("Back to Menu"):
                reset_to_main_menu()
        with col4:
            if st.button("Play Again"):
                st.session_state['langraph_state']['number_range'] = (1, 50)
                st.session_state['langraph_state']['attempts'] = 0
                st.session_state['langraph_state']['mid'] = (st.session_state['langraph_state']['low'] + st.session_state['langraph_state']['high']) // 2
                st.session_state['langraph_state']['game_over'] = False
                st.session_state["question"] = "Welcome to the Number Game! Think of a number between 1 and 50.\nIs your number greater than 25?"
                st.session_state["message"] = ""
                st.rerun()
        with col5:
            if st.button("Try Word Game"):
                switch_to_game('word')

def play_word_game():
    st.subheader("🧠 Word Guessing Game")
    
    # Initialize all required session state variables
    if ('langraph_state' not in st.session_state or 
        st.session_state.langraph_state.get('mode') != 'word' or
        'word_game_initialized' not in st.session_state):
        
        st.session_state['langraph_state'] = initialize_state()
        st.session_state['langraph_state']['mode'] = 'word'
        st.session_state['word_game_initialized'] = True
        st.session_state["word_game_step"] = 0
        st.session_state["asked_categories"] = []
        st.session_state["last_question"] = None
        st.session_state["should_guess"] = False
        st.session_state["message"] = ""
        st.session_state["word_options"] = list(word_categories.keys())

    state = st.session_state['langraph_state']
    possible_words = st.session_state.get("word_options", list(word_categories.keys()))
    asked_categories_state = st.session_state.get("asked_categories", [])
    
    # Display game info
    st.write("🧠 Welcome to the Word Game!")
    st.write("Think of one of these words:")
    st.write(", ".join(word_categories.keys()))
    
    # Display success message if game is over
    if state.get('game_over', False):
        st.success(st.session_state.get("message", ""))
        
        # Game over buttons - matching number game layout
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔄 Play Again"):
                st.session_state.pop('word_game_initialized', None)
                st.session_state.pop('langraph_state', None)
                st.session_state.pop("word_game_step", None)
                st.session_state.pop("asked_categories", None)
                st.session_state.pop("should_guess", None)
                st.session_state.pop("message", None)
                st.session_state.pop("word_options", None)
                st.rerun()
        with col2:
            if st.button("🔢 Try Number Game"):
                switch_to_game('number')
        with col3:
            if st.button("🏠 Back to Menu"):
                reset_to_main_menu()
        with col4:
            if st.button("🚪 Exit Game"):
                st.session_state.game['mode'] = 'exit'
                st.rerun()
        return
    
    # Get remaining categories
    remaining_categories = []
    for word in possible_words:
        if word in word_categories:
            for category in word_categories[word]:
                if category not in asked_categories_state and category not in remaining_categories:
                    remaining_categories.append(category)
    remaining_categories = sorted(remaining_categories)

    # Find the best category to ask about
    best_category = None
    best_score = -1
    for category in remaining_categories:
        yes_count = sum(1 for word in possible_words if word in word_categories and category in word_categories[word])
        no_count = len(possible_words) - yes_count
        score = min(yes_count, no_count)
        if score > best_score:
            best_score = score
            best_category = category

    # Gameplay section
    if not st.session_state.get("should_guess", False) and best_category and len(possible_words) > 1:
        # Ask category question phase
        st.write(f"🧐 Is your word related to '{best_category}'?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Yes"):
                st.session_state['asked_categories'] = asked_categories_state + [best_category]
                updated_possible_words = [word for word in possible_words 
                                       if word in word_categories and best_category in word_categories[word]]
                st.session_state['word_options'] = updated_possible_words
                st.session_state["word_game_step"] += 1
                st.session_state["should_guess"] = True
                st.rerun()
        with col2:
            if st.button("👎 No"):
                st.session_state['asked_categories'] = asked_categories_state + [best_category]
                updated_possible_words = [word for word in possible_words 
                                       if word in word_categories and best_category not in word_categories[word]]
                st.session_state['word_options'] = updated_possible_words
                st.session_state["word_game_step"] += 1
                st.session_state["should_guess"] = True
                st.rerun()
    
    elif st.session_state.get("should_guess", False) and possible_words:
        # Make a guess phase
        guess = random.choice(possible_words)
        st.write(f"🤔 Is your word '{guess}'?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, you got it!"):
                st.session_state['langraph_state']['game_over'] = True
                st.session_state["message"] = f"🎉 I guessed it! Your word is '{guess}'!"
                st.rerun()
        with col2:
            if st.button("❌ No, try again"):
                updated_possible_words = [word for word in possible_words if word != guess]
                st.session_state['word_options'] = updated_possible_words
                st.session_state["should_guess"] = False
                
                if not updated_possible_words:
                    st.session_state['langraph_state']['game_over'] = True
                    st.session_state["message"] = "😢 I ran out of guesses."
                st.rerun()
    
    else:
        # Final guess when no more categories
        if possible_words:
            guess = random.choice(possible_words)
            st.write(f"🤔 Is your word '{guess}'?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, you got it!"):
                    st.session_state['langraph_state']['game_over'] = True
                    st.session_state["message"] = f"🎉 I guessed it! Your word is '{guess}'!"
                    st.rerun()
            with col2:
                if st.button("❌ No, try again"):
                    updated_possible_words = [word for word in possible_words if word != guess]
                    st.session_state['word_options'] = updated_possible_words
                    
                    if not updated_possible_words:
                        st.session_state['langraph_state']['game_over'] = True
                        st.session_state["message"] = "😢 I ran out of guesses."
                    st.rerun()
        else:
            st.session_state['langraph_state']['game_over'] = True
            st.session_state["message"] = "😢 I ran out of guesses."
            st.rerun()
    
    # Navigation buttons during gameplay - matching number game layout
    if not state.get('game_over', False):
        st.write("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🚪 Exit Game"):
                st.session_state.game['mode'] = 'exit'
                st.rerun()
        with col2:
            if st.button("🏠 Back to Menu"):
                reset_to_main_menu()
        with col3:
            if st.button("🔢 Try Number Game"):
                switch_to_game('number')
        with col4:
            if st.button("🔄 Play Again"):
                st.session_state.pop('word_game_initialized', None)
                st.session_state.pop('langraph_state', None)
                st.session_state.pop("word_game_step", None)
                st.session_state.pop("asked_categories", None)
                st.session_state.pop("should_guess", None)
                st.session_state.pop("message", None)
                st.session_state.pop("word_options", None)
                st.rerun()

def reset_to_main_menu():
    st.session_state.game['mode'] = None
    st.session_state.pop('langraph_state', None)
    st.session_state.pop("question", None)
    st.session_state.pop("message", None)
    st.session_state.pop("response", None)
    st.session_state.pop("word_game_step", None)
    st.session_state.pop("asked_categories_ui", None)
    st.rerun()

def switch_to_game(mode):
    st.session_state.game['mode'] = mode
    st.session_state['langraph_state'] = initialize_state()
    st.session_state['langraph_state']['mode'] = mode
    if mode == 'number':
        st.session_state['langraph_state']['next_node'] = 'number_game' # Ensure number game starts
        st.session_state["question"] = "Welcome to the Number Game! Think of a number between 1 and 50.\nIs your number greater than 25?" # Set initial question
    st.session_state.pop("message", None)
    st.session_state.pop("response", None)
    st.session_state.pop("word_game_step", None)
    st.session_state.pop("asked_categories_ui", None)
    st.rerun()

def main():
    st.set_page_config(page_title="Game Challenge", page_icon="🎲")
    figlet = Figlet(font='slant')
    st.markdown(f"<pre style='color:cyan'>{figlet.renderText('Game Zone')}</pre>", unsafe_allow_html=True)
    st.title("🎮 Welcome to the Game Challenge!")

    if 'game' not in st.session_state:
        st.session_state.game = {'mode': None, 'number_range': (1, 50), 'attempts': 0, 'games_played': 0, 'word_options': None, 'asked_categories': [], 'current_guess': None}

    mode = st.session_state.game['mode']
    if mode is None:
        show_game_menu()
    elif mode == 'number':
        play_number_game()
    elif mode == 'word':
        play_word_game()
    elif mode == 'exit':
        st.success("👋 Thanks for playing! Come back soon.")

if __name__ == "__main__":
    main()

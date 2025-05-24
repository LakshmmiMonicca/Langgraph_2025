from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Tuple, Literal
import random
import time
from colorama import init, Fore, Style
from pyfiglet import Figlet

init(autoreset=True)  # Reset colors after each print


# -----------------------------
# State Definition
# -----------------------------
class GameState(TypedDict):
    game_choice: Optional[str]
    game_mode: Optional[str]
    game_count: int
    message: str
    guess_range: Tuple[int, int]
    attempts: int
    asked_categories: list[str]
    possible_words: list[str]
    next_node: Optional[str]

def initialize_state() -> GameState:
    return {
        "game_choice": None,
        "game_mode": None,
        "game_count": 0,
        "message": "",
        "guess_range": (1, 50),
        "attempts": 0,
        "asked_categories": [],
        "possible_words": [],
        "next_node": "game_selector"
    }

# -----------------------------
# Game Selector Node (Updated)
# -----------------------------
def game_selector(state: GameState) -> GameState:
    print(Fore.GREEN + "\n🎮 " + Style.BRIGHT + "Choose a game:" + Style.RESET_ALL)
    print(Fore.CYAN + Style.BRIGHT + " 1️⃣  Number Game")
    print(Fore.CYAN + Style.BRIGHT + " 2️⃣  Word Game")
    print(Fore.RED + Style.BRIGHT + " 3️⃣  Exit")
    print()
    choice = input(Fore.YELLOW + Style.BRIGHT + "👉 Enter your choice (1/2/3): " + Style.RESET_ALL).strip()


    if choice == "1":
        print(Fore.LIGHTBLUE_EX + "🔢 Starting Number Game...\n")
        state["game_choice"] = "number_game"
        state["game_mode"] = "number_game"
        state["next_node"] = "number_game"
    elif choice == "2":
        print(Fore.LIGHTBLUE_EX + "🧠 Starting Word Game...\n")
        state["game_choice"] = "word_game"
        state["game_mode"] = "word_game"
        state["next_node"] = "word_game"
    elif choice == "3":
        print(Fore.RED + "👋 Exiting the game. Thanks for playing!")
        state["next_node"] = None
    else:
        print(Fore.RED + "❌ Invalid choice. Try again.")
        state["next_node"] = "game_selector"

    time.sleep(1)
    return state


# -----------------------------
# Number Game Node
# -----------------------------
def number_game(state: GameState) -> GameState:
    print(Fore.BLUE + Style.BRIGHT + "\n🔢 Welcome to the Number Game!")
    print("🤔 Think of a number between " + Fore.YELLOW + "1" + Style.RESET_ALL + " and " + Fore.YELLOW + "50" + Style.RESET_ALL)
    low, high = state["guess_range"]

    while low < high:
        mid = (low + high) // 2
        user_response = input(Fore.CYAN + f"🧠 Is your number greater than {mid}? (yes/no): ").strip().lower()
        state["attempts"] += 1

        if user_response == "yes":
            low = mid + 1
        elif user_response == "no":
            high = mid
        else:
            print("Invalid input.")
            continue

        if low == high:
            print(Fore.GREEN + f"🎉 I guessed it! Your number is {low}!")
            break
        
    print(Fore.LIGHTBLUE_EX + "🔄 Loading the next challenge...")
    time.sleep(1.2)
    
    state["guess_range"] = (1, 50)
    state["attempts"] = 0
    state["game_count"] += 1
    state["next_node"] = "game_selector" if state["game_count"] < 5 else "end"
    return state

# -----------------------------
# Word Game Node
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
all_categories = sorted({cat for tags in word_categories.values() for cat in tags})

def word_game(state: GameState) -> GameState:
    print(Fore.BLUE + Style.BRIGHT + "\n🧠 Welcome to the Word Game!")
    print(Fore.LIGHTMAGENTA_EX + "Think of one of these words:")
    print(Fore.YELLOW + ", ".join(word_categories.keys()) + "\n")
    state["possible_words"] = list(word_categories.keys())
    state["asked_categories"] = []
    state["attempts"] = 0

    for _ in range(5):
        remaining = [c for c in all_categories if c not in state["asked_categories"]]
        if not remaining:
            break
        category = random.choice(remaining)
        state["asked_categories"].append(category)

        clue = input(Fore.CYAN + f"🧐 Is your word related to '{category}'? (yes/no): ").strip().lower()
        state["attempts"] += 1

        if clue == "yes":
            state["possible_words"] = [
                word for word in state["possible_words"] if category in word_categories[word]
            ]
        elif clue == "no":
            state["possible_words"] = [
                word for word in state["possible_words"] if category not in word_categories[word]
            ]
        else:
            print("Invalid input.")
            continue

        if state["possible_words"]:
            guess = random.choice(state["possible_words"])
            confirm = input(Fore.YELLOW + f"🤔 Is your word '{guess}'? (yes/no): ").strip().lower()
            if confirm == "yes":
                print(Fore.GREEN + f"🎉 I guessed it! Your word is '{guess}'!")
                break
            else:
                state["possible_words"].remove(guess)

    if not state["possible_words"]:
        print(Fore.RED + "😢 I couldn't guess your word.")

    print(Fore.LIGHTBLUE_EX + "🔄 Loading the next challenge...")
    time.sleep(1.2)

    state["game_count"] += 1
    state["next_node"] = "game_selector" if state["game_count"] < 5 else "end"
    return state

# -----------------------------
# LangGraph Setup
# -----------------------------
def router(state: GameState) -> str:
    return state["next_node"] if state["next_node"] else END

def build_game_graph():
    builder = StateGraph(GameState)

    builder.add_node("game_selector", game_selector)
    builder.add_node("number_game", number_game)
    builder.add_node("word_game", word_game)

    builder.set_entry_point("game_selector")
    builder.add_conditional_edges("game_selector", router)
    builder.add_conditional_edges("number_game", router)
    builder.add_conditional_edges("word_game", router)

    #builder.add_edge("end", END)
    return builder.compile()

# -----------------------------
# Run the Game
# -----------------------------
if __name__ == "__main__":
    figlet = Figlet(font='slant')
    print(Fore.CYAN + figlet.renderText('Game Zone'))

    print(Fore.MAGENTA + "🎲 Welcome to the Multi-Game Challenge! 🎲\n")
    time.sleep(1)

    graph = build_game_graph()
    state = initialize_state()
    graph.invoke(state)

    print(Fore.YELLOW + Style.BRIGHT + "\n🎮 Thank you for playing! See you next time!\n")

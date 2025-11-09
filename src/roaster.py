import random

# --- Simplified ROASTS dictionary ---
ROASTS = {
    'angry': [
        "Hey {player_name}, why so angry?",
        "Whoa, {player_name}, it's just a game. Relax.",
        "{player_name}, you're scaring the webcam.",
        "Looks like {player_name} is about to rage-quit.",
        "I've seen toddlers handle losing better than you, {player_name}."
    ],
    'sad': [
        "Aw, {player_name}, don't cry. You'll get 'em next time... maybe.",
        "Cheer up, {player_name}. It's not like you were going to win anyway."
    ],
    'surprised': [
        "What's wrong, {player_name}? Did you actually land a hit?",
        "That's the 'I definitely messed up' face, {player_name}."
    ],
    'default': [
        "You okay over there, {player_name}?",
        "I'm just going to pretend I didn't see that."
    ]
}

PLAYER_NAMES = {
    'left': "fella on the left",
    'right': "fella on the right",
    'all': "all you scrubs" # Fallback
}

# --- THIS IS YOUR CONTRACT WITH MAIN.PY ---

class RoastMaster:
    """
    Generates and formats roasts.
    """
    def __init__(self):
        print("Audio: RoastMaster Initialized.")
        pass

    def get_roast(self, emotion_key, player_id):
        """
        Gets a random roast, formatted for the specific player.
        
        Args:
            emotion_key (str): The emotion or trigger ('angry', 'sad')
            player_id (str): The player to roast ('left', 'right', 'all')
        """

        # 1. Get the player's "name"
        player_name = PLAYER_NAMES.get(player_id, "you")

        # 2. Get the list of roasts
        if emotion_key in ROASTS:
            roast_list = ROASTS[emotion_key]
        else:
            roast_list = ROASTS['default']

        # 3. Pick a random template
        roast_template = random.choice(roast_list)
        
        # 4. Format the template with the player's name and return it
        final_roast = roast_template.format(player_name=player_name)
        
        return final_roast
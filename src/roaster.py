import random
class RoastMaster:
    """
    Generates context-aware roasts based on player emotion and trigger type.
    """
    
    # Dictionary of roasts organized by category
    ROASTS = {
        'angry': [
            "You're selling",
            "Catching Ls only",
            "You're trash kid", 
            "Labronzo hop that ahh back on roblox",
            "Pack it up",
            "You're cooked",
            "You're trolling",
            "Absolutely washed",
            "That's embarrassing",
            "Delete the game"
        ],

        'sad': [
            "Pack it up, it's bedtime",
            "Someone call this man's therapist",
            "Bro's getting emotional over pixels",
            "The game hurt your feelings that bad?",
            "You look like you just lost your lunch money",
            "Depression speedrun any percent",
            "Catching feelings and catching Ls",
            "You're one loss away from tears",
            "Emotional damage detected",
            "This ain't it chief, go take a break"
        ],

        'shake': [
            "Did you drop the controller? Skill issue.",
            "Stop shaking, your rage is pathetic.",
            "Take a deep breath, or maybe a nap.",
        ],

        'yell': [
            "Nobody cares about your sound effects, mute your mic.",
            "Your voice is cracking, is that the sound of a breakdown?",
            "Volume is not a measure of skill, kid.",
        ],
       
        'neutral': [
            "You're playing like your monitor is off",
            "Is this your first time touching a controller?",
            "You're selling harder than a Black Friday sale",
            "Absolutely washed",
            "Delete the game",
            "You're cooked",
            "Catching Ls only",
            "That's embarrassing",
            "You're trolling right now",
            "Pack it up"
        ]
    }
    
    def __init__(self):
        """Initialize the RoastMaster."""
        pass
    
    def get_roast(self, emotion_key='neutral', player_id='unknown'):
        """
        Get a random roast from the specified category.
        
        Args:
            category (str): The type of roast ('angry', 'sad', 'shake', 'yell', 'neutral')
            player (str): Player identifier ('left', 'right', 'all', or player name)
        
        Returns:
            str: A roast string with player name filled in if applicable
        """
        # Get roasts for the category, default to neutral if category not found
        roast_list = self.ROASTS.get(emotion_key, self.ROASTS['neutral'])
        
        # Pick a random roast
        roast = random.choice(roast_list)
        
        # Add player context if needed
        if player_id == 'left':
            roast = f"Player 1: {roast}"
        elif player_id == 'right':
            roast = f"Player 2: {roast}"
        
        return roast


# --- Standalone function for easy testing ---
def get_roasts(category='neutral'):
    """
    Simple function that returns a random roast.
    Used for testing and backwards compatibility.
    
    Args:
        category (str): The roast category
    
    Returns:
        str: A random roast
    """
    roaster = RoastMaster()
    return roaster.get_roast(category)


# --- Test the roaster ---
if __name__ == "__main__":
    print("=== ROAST MASTER TEST ===\n")
    
    roaster = RoastMaster()
    
    # Test each category
    categories = ['angry', 'sad', 'shake', 'yell', 'neutral']
    
    for category in categories:
        print(f"\n--- {category.upper()} ROASTS ---")
        for i in range(3):
            print(f"{i+1}. {roaster.get_roast(category, 'left')}")
    
    print("\n=== TEST COMPLETE ===")

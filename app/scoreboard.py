# scoreboard.py
import json
import os

LEADERBOARD_FILE = "leaderboard.json"


def get_leaderboard():
    """Load the leaderboard from file, returning a list of top scores sorted by score desc."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    with open(LEADERBOARD_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []
    # Sort the list of scores in descending order by score
    data.sort(key=lambda entry: entry.get("score", 0), reverse=True)
    return data[:10]  # return top 10 entries


def save_score(name, score):
    """Save a new score (name and score) to the leaderboard file."""
    # Load existing data
    scores = get_leaderboard()
    # Append new score and resort
    scores.append({"name": name, "score": score})
    scores.sort(key=lambda entry: entry.get("score", 0), reverse=True)
    # Keep only top 10
    scores = scores[:10]
    # Write back to the JSON file
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(scores, f)

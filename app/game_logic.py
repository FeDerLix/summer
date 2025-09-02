# game_logic.py
import random

def initialize_game(mode, player_names):
    """
    Create a new game state for the given mode ('solo' or 'multi') and players.
    Each player starts with default stats.
    """
    players = []
    for name in player_names:
        players.append({
            "name": name,
            "money": 5000,         # starting cash
            "customers": 100,      # starting customer count
            "employees": 5,        # starting employees
            "product": 50,         # product quality (0-100)
            "reputation": 50       # reputation (0-100)
        })
    # Game state dictionary to track progress
    state = {
        "mode": mode,                # 'solo' or 'multi'
        "players": players,          # list of player stats
        "month": 1,                  # current month (1-12)
        "current_player": 0,         # index of whose turn it is (for multi-mode)
        "history": [],               # full log (always used & shown in solo)
        "round_history": [],         # shown ONLY in multiplayer (current round)
        "round_history_month": 0,    # month that round_history belongs to
        # --- NEW: chart time series (per player) ---
        "step": 0,                   # action counter across the whole game
        "timeseries": [[] for _ in players],  # each entry: list of {x: step, y: money}
    }

    # Seed the chart with initial money at step 0
    for i, p in enumerate(players):
        state["timeseries"][i].append({"x": 0, "y": p["money"]})

    return state


def apply_action(game_state, action):
    """
    Apply the chosen action for the current player, update game state for that turn,
    and advance to the next turn (and possibly trigger random events at end of month).
    """
    # Backward-compat for older sessions
    if "round_history" not in game_state:
        game_state["round_history"] = []
    if "round_history_month" not in game_state:
        game_state["round_history_month"] = 0
    if "step" not in game_state:
        game_state["step"] = 0
    if "timeseries" not in game_state:
        game_state["timeseries"] = [[] for _ in game_state["players"]]
        for i, p in enumerate(game_state["players"]):
            game_state["timeseries"][i].append({"x": 0, "y": p["money"]})

    idx = game_state["current_player"]
    player = game_state["players"][idx]

    # --- Multiplayer: clear the round display only at the START of a new month ---
    if game_state["mode"] == "multi":
        if idx == 0 and game_state["round_history_month"] != game_state["month"]:
            game_state["round_history"].clear()
            game_state["round_history_month"] = game_state["month"]

    # Base monthly financial parameters
    revenue_per_customer_base = 10
    revenue_per_quality_factor = 0.5    # each product point increases revenue/customer
    cost_per_employee = 300             # monthly salary cost per employee

    # Calculate this month's revenue and salary expenses for the player
    revenue = int(player["customers"] * (revenue_per_customer_base +
                  revenue_per_quality_factor * player["product"]))
    salary_cost = player["employees"] * cost_per_employee

    # Prepare a description of the action and outcome for the logs
    desc = f"{player['name']} "
    if action == "marketing":
        cost = 1000
        player["money"] -= cost
        new_cust = random.randint(20, 50)
        player["customers"] += new_cust
        rep_gain = random.randint(1, 3)
        player["reputation"] = min(100, player["reputation"] + rep_gain)
        desc += f"ran a marketing campaign, gaining {new_cust} customers (cost ${cost})."
    elif action == "product":
        cost = 800
        player["money"] -= cost
        quality_gain = random.randint(5, 10)
        player["product"] = min(100, player["product"] + quality_gain)
        rep_gain = random.randint(1, 2)
        player["reputation"] = min(100, player["reputation"] + rep_gain)
        desc += f"invested in product development, improving quality by {quality_gain} (cost ${cost})."
    elif action == "hiring":
        cost = 500
        player["money"] -= cost
        new_emp = random.choice([1, 1, 2])
        player["employees"] += new_emp
        player["reputation"] = min(100, player["reputation"] + 1)
        desc += f"hired {new_emp} new employee(s) (cost ${cost})."
    else:
        cost = 0
        desc += "took no new action this month."

    # Apply monthly revenue and expenses to money
    player["money"] += revenue
    player["money"] -= salary_cost

    # If understaffed relative to customers, reputation can drop (poor service)
    if player["customers"] > player["employees"] * 20:
        player["reputation"] = max(0, player["reputation"] - 1)

    # Compute net profit/loss this turn
    net_profit = revenue - salary_cost - cost
    if net_profit >= 0:
        desc += f" Revenue ${revenue} - Expenses ${salary_cost + cost} ⇒ Net **+${net_profit}**."
    else:
        desc += f" Revenue ${revenue} - Expenses ${salary_cost + cost} ⇒ Net **-${-net_profit}**."

    # --- Logging ---
    # Always keep full history (used by solo view)
    game_state["history"].append(desc)

    # Only maintain round_history in MULTI
    if game_state["mode"] == "multi":
        game_state["round_history"].append(desc)
        # Keep at most N entries for this round (N = number of players)
        limit = len(game_state["players"])
        if len(game_state["round_history"]) > limit:
            game_state["round_history"] = game_state["round_history"][-limit:]

    # --- Chart series update (per player, after action) ---
    game_state["step"] += 1
    game_state["timeseries"][idx].append({"x": game_state["step"], "y": player["money"]})

    # --- Advance turn / month and maybe trigger an event ---
    num_players = len(game_state["players"])
    if num_players > 1:
        # Multiplayer
        if game_state["current_player"] < num_players - 1:
            # Next player's turn within the same month
            game_state["current_player"] += 1
        else:
            # Last player of the month has played; end of month
            game_state["current_player"] = 0
            game_state["month"] += 1

            # End-of-month random event (add to full history)
            event = _random_event(game_state)
            if event:
                game_state["history"].append(event)

            # Do NOT clear round_history here; we clear at the next month's first turn
    else:
        # Solo: one action per month then advance (solo view uses full history)
        game_state["month"] += 1
        event = _random_event(game_state)
        if event:
            game_state["history"].append(event)

    return game_state


def _random_event(game_state):
    """
    Possibly trigger a random event that can affect one or all companies.
    Returns a description string of the event if one occurred, or None otherwise.
    """
    # 20% chance for a random event each month
    if random.random() < 0.20:
        events = ["boom", "recession", "fine", "viral"]
        ev = random.choice(events)
        if ev == "boom":
            for p in game_state["players"]:
                increase = max(1, int(p["customers"] * 0.15))
                p["customers"] += increase
            return "📈 **Economic Boom!** The market expanded and all companies gained roughly 15% more customers."
        elif ev == "recession":
            for p in game_state["players"]:
                loss = int(p["customers"] * 0.10)
                p["customers"] = max(0, p["customers"] - loss)
            return "📉 **Recession!** An economic downturn caused all companies to lose about 10% of their customers."
        elif ev == "fine":
            victim = random.choice(game_state["players"])
            fine_amount = 1000
            victim["money"] = max(0, victim["money"] - fine_amount)
            return f"⚖️ **Legal Fine!** {victim['name']} was fined ${fine_amount} due to a legal issue."
        elif ev == "viral":
            winner = random.choice(game_state["players"])
            winner["customers"] += 50
            winner["reputation"] = min(100, winner["reputation"] + 5)
            return f"🔥 **Viral Buzz!** {winner['name']}'s product went viral, adding 50 new customers and boosting reputation."
    return None

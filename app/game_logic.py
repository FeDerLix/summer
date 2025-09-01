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
    return {
        "mode": mode,            # 'solo' or 'multi'
        "players": players,      # list of player stats
        "month": 1,              # current month (1-12)
        "current_player": 0,     # index of whose turn it is (for multi-mode)
        "history": []            # log of events/descriptions for each action
    }

#hello felix
def apply_action(game_state, action):
    """
    Apply the chosen action for the current player, update game state for that turn,
    and advance to the next turn (and possibly trigger random events at end of month).
    """
    idx = game_state["current_player"]
    player = game_state["players"][idx]
    # Base monthly financial parameters
    revenue_per_customer_base = 10
    # each point of product quality increases revenue per customer
    revenue_per_quality_factor = 0.5
    cost_per_employee = 300            # monthly cost per employee (salary)

    # Calculate this month's revenue and salary expenses for the player
    revenue = int(player["customers"] * (revenue_per_customer_base +
                  revenue_per_quality_factor * player["product"]))
    salary_cost = player["employees"] * cost_per_employee

    # Prepare a description of the action and outcome for the history log
    desc = f"{player['name']} "
    if action == "marketing":
        # Marketing: spend money to gain new customers and boost reputation slightly
        cost = 1000
        player["money"] -= cost
        new_cust = random.randint(20, 50)         # acquire 20-50 new customers
        player["customers"] += new_cust
        rep_gain = random.randint(1, 3)           # small reputation boost
        player["reputation"] = min(100, player["reputation"] + rep_gain)
        desc += f"ran a marketing campaign, gaining {new_cust} customers (cost ${cost})."
    elif action == "product":
        # Product development: invest money to improve product quality (and rep)
        cost = 800
        player["money"] -= cost
        # improve product quality by 5-10
        quality_gain = random.randint(5, 10)
        player["product"] = min(100, player["product"] + quality_gain)
        rep_gain = random.randint(1, 2)           # slight reputation increase
        player["reputation"] = min(100, player["reputation"] + rep_gain)
        desc += f"invested in product development, improving quality by {quality_gain} (cost ${cost})."
    elif action == "hiring":
        # Hiring: spend money to add an employee (increases capacity, affects costs)
        cost = 500
        player["money"] -= cost
        # hire 1 (or sometimes 2) new employees
        new_emp = random.choice([1, 1, 2])
        player["employees"] += new_emp
        # slight rep increase for better service
        player["reputation"] = min(100, player["reputation"] + 1)
        desc += f"hired {new_emp} new employee(s) (cost ${cost})."
    else:
        # Doing nothing: no direct costs or gains from action
        cost = 0
        desc += "took no new action this month."

    # Apply monthly revenue and expenses to money
    player["money"] += revenue            # add revenue
    # subtract salary expenses for employees
    player["money"] -= salary_cost

    # If the company is understaffed relative to customers, reputation can drop (poor service).
    if player["customers"] > player["employees"] * 20:
        player["reputation"] = max(0, player["reputation"] - 1)

    # Compute net profit/loss this turn (revenue minus all expenses including action cost)
    net_profit = revenue - salary_cost - cost
    if net_profit >= 0:
        desc += f" Revenue ${revenue} - Expenses ${salary_cost +cost} ⇒ Net **+${net_profit}**."
    else:
        desc += f" Revenue ${revenue} - Expenses ${salary_cost +cost} ⇒ Net **-${-net_profit}**."

    # Add the description of this turn to the history log
    game_state["history"].append(desc)

    # Advance to next player or next month
    num_players = len(game_state["players"])
    if num_players > 1:
        # Multiplayer: move to next player’s turn
        if game_state["current_player"] < num_players - 1:
            game_state["current_player"] += 1
        else:
            # Last player of the month has played; end of month events, then next month
            game_state["current_player"] = 0
            game_state["month"] += 1
            # Check for a random event at end of the month
            event = _random_event(game_state)
            if event:
                game_state["history"].append(event)
    else:
        # Solo mode: only one player per month, so increment month after action
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
            # Economic boom: all companies gain +15% customers
            for p in game_state["players"]:
                increase = max(1, int(p["customers"] * 0.15))
                p["customers"] += increase
            return "📈 **Economic Boom!** The market expanded and all companies gained roughly 15% more customers."
        elif ev == "recession":
            # Recession: all companies lose 10% customers
            for p in game_state["players"]:
                loss = int(p["customers"] * 0.10)
                p["customers"] = max(0, p["customers"] - loss)
            return "📉 **Recession!** An economic downturn caused all companies to lose about 10% of their customers."
        elif ev == "fine":
            # Legal fine: one random company pays a fine
            victim = random.choice(game_state["players"])
            fine_amount = 1000
            victim["money"] = max(0, victim["money"] - fine_amount)
            return f"⚖️ **Legal Fine!** {victim['name']} was fined ${fine_amount} due to a legal issue."
        elif ev == "viral":
            # Viral trend: one company gets a surge in popularity
            winner = random.choice(game_state["players"])
            winner["customers"] += 50
            winner["reputation"] = min(100, winner["reputation"] + 5)
            return f"🔥 **Viral Buzz!** {winner['name']}'s product went viral, adding 50 new customers and boosting reputation."
    return None

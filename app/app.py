# app.py
from flask import Flask, session, redirect, url_for, render_template, request
from game_logic import initialize_game, apply_action
from scoreboard import get_leaderboard, save_score

app = Flask(__name__)
# Secret key for sessions (set a real secret in production)
app.secret_key = 'CHANGE_THIS_SECRET'


@app.route('/')
def index():
    """Main menu – choose Solo or Multiplayer mode."""
    return render_template('index.html')


@app.route('/solo', methods=['GET', 'POST'])
def solo():
    """Solo mode setup – ask for player's name, then start a solo game."""
    if request.method == 'POST':
        player_name = request.form['player_name']
        # Initialize a new solo game with the given player name
        game_state = initialize_game('solo', [player_name])
        session['game'] = game_state  # store game state in session
        return redirect(url_for('game'))
    # GET request: render the form to enter player name
    return render_template('solo.html')


@app.route('/multiplayer', methods=['GET', 'POST'])
def multiplayer():
    """Multiplayer setup – choose number of players and enter their names."""
    if request.method == 'POST':
        num_players = int(request.form['num_players'])
        names = []
        # Collect the specified number of player names from the form
        for i in range(1, num_players + 1):
            name_field = request.form.get(f'name{i}')
            if name_field and name_field.strip():
                names.append(name_field.strip())
            else:
                # If a name is left blank, assign a default name
                names.append(f"Player {i}")
        # Initialize a new multiplayer game with these names
        game_state = initialize_game('multi', names)
        session['game'] = game_state
        return redirect(url_for('game'))
    # GET request: render the form for multiplayer setup
    return render_template('multiplayer.html')


@app.route('/game', methods=['GET', 'POST'])
def game():
    """Main game loop – display current state and handle actions each turn."""
    game_state = session.get('game')
    if game_state is None:
        # If no game in session (e.g. user refreshed or came here directly), go to main menu
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Handle the action chosen by the player
        action = request.form.get('action')
        if action:
            # Update the game state with the chosen action
            game_state = apply_action(game_state, action)
            session['game'] = game_state  # save updated state
        # Check if the game has finished (month 13 means after month 12)
        if game_state['month'] > 12:
            return redirect(url_for('summary'))
        # Otherwise, continue to next turn
        return redirect(url_for('game'))

    # GET request: render the game interface with the current state
    return render_template('game.html', game=game_state)


@app.route('/summary')
def summary():
    """Game over – show final stats and determine winner, save score if solo."""
    game_state = session.get('game')
    if game_state is None:
        return redirect(url_for('index'))
    # If solo game, save the score to the leaderboard
    if game_state['mode'] == 'solo':
        player = game_state['players'][0]
        save_score(player['name'], player['money'])
    # Determine winner in multiplayer (player with highest money)
    winner_name = None
    winner_money = None
    if game_state['mode'] == 'multi':
        winner = max(game_state['players'], key=lambda p: p['money'])
        winner_name = winner['name']
        winner_money = winner['money']
    # Prepare data for the summary template
    players = game_state['players']
    # Clear game from session now that it's over (optional)
    session.pop('game', None)
    return render_template('summary.html', players=players, mode=game_state['mode'],
                           winner_name=winner_name, winner_money=winner_money)


@app.route('/leaderboard')
def leaderboard():
    """Display the top scores from solo mode games."""
    top_scores = get_leaderboard()
    return render_template('leaderboard.html', leaderboard=top_scores)


app.run()

test

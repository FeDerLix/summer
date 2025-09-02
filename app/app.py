# app.py
from flask import Flask, session, redirect, url_for, render_template, request
from game_logic import initialize_game, apply_action
from scoreboard import get_leaderboard, save_score
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'CHANGE_THIS_SECRET'

# Dev-friendly reloads
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.cache = {}

# Jinja filter to format ISO timestamps to 'YYYY-MM-DD HH:MM'
@app.template_filter('fmt_dt')
def fmt_dt(value):
    try:
        if isinstance(value, str) and value.endswith('Z'):
            value = value[:-1] + '+00:00'
        dt = datetime.fromisoformat(value) if isinstance(value, str) else value
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return value


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/solo', methods=['GET', 'POST'])
def solo():
    if request.method == 'POST':
        player_name = request.form['player_name']
        game_state = initialize_game('solo', [player_name])
        session['game'] = game_state
        return redirect(url_for('game'))
    return render_template('solo.html')


@app.route('/multiplayer', methods=['GET', 'POST'])
def multiplayer():
    if request.method == 'POST':
        num_players = int(request.form['num_players'])
        names = []
        for i in range(1, num_players + 1):
            name_field = request.form.get(f'name{i}')
            names.append(name_field.strip() if name_field and name_field.strip() else f"Player {i}")
        game_state = initialize_game('multi', names)
        session['game'] = game_state
        return redirect(url_for('game'))
    return render_template('multiplayer.html')


@app.route('/game', methods=['GET', 'POST'])
def game():
    game_state = session.get('game')
    if game_state is None:
        return redirect(url_for('index'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action:
            game_state = apply_action(game_state, action)
            session['game'] = game_state
        if game_state['month'] > 12:
            return redirect(url_for('summary'))
        return redirect(url_for('game'))

    return render_template('game.html', game=game_state)


@app.route('/summary')
def summary():
    game_state = session.get('game')
    if game_state is None:
        return redirect(url_for('index'))

    # --- SOLO: save single player's result ---
    if game_state['mode'] == 'solo':
        p = game_state['players'][0]
        meta = {
            "mode": "solo",
            "players": 1,
            "customers": p.get('customers'),
            "employees": p.get('employees'),
            "product": p.get('product'),
            "reputation": p.get('reputation'),
        }
        save_score(p['name'], p['money'], meta=meta)

    # --- MULTI: save ALL players' results (changed as requested) ---
    winner_name = None
    winner_money = None
    if game_state['mode'] == 'multi':
        # Save each player's score
        for p in game_state['players']:
            meta = {
                "mode": "multi",
                "players": len(game_state['players']),
                "customers": p.get('customers'),
                "employees": p.get('employees'),
                "product": p.get('product'),
                "reputation": p.get('reputation'),
            }
            save_score(p['name'], p['money'], meta=meta)

        # Still compute winner for the summary view
        winner = max(game_state['players'], key=lambda x: x['money'])
        winner_name = winner['name']
        winner_money = winner['money']

    players = game_state['players']
    session.pop('game', None)
    return render_template('game_over.html', players=players, mode=game_state['mode'],
                           winner_name=winner_name, winner_money=winner_money)


# --- Leaderboards ---
# If you want /leaderboard to jump straight to Solo, keep this redirect:
@app.route('/leaderboard')
def leaderboard_index():
    return redirect(url_for('leaderboard_solo'))

@app.route('/leaderboard/solo')
def leaderboard_solo():
    top_scores = get_leaderboard(mode='solo')
    return render_template('leaderboard.html',
                           title="Leaderboard – Top Solo Game Scores",
                           leaderboard=top_scores)

@app.route('/leaderboard/multi')
def leaderboard_multi():
    top_scores = get_leaderboard(mode='multi')
    return render_template('leaderboard.html',
                           title="Leaderboard – Top Multiplayer Game Scores",
                           leaderboard=top_scores)


if __name__ == "__main__":
    app.run(debug=True)

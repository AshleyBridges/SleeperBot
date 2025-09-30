# import things
import requests
import sys
import argparse
import json
from config import WEBHOOK_URL, leagues


weekly_challenge = {
    1: '*New Season, Still Bad* - Lowest final score.',
    2: '*The Icarus Award* - Largest negative point differential from last week to this week.',
    3: '*Benchwarmer* - Most total points on the bench.',
    4: '*Run Like the Wind* - Highest total rushing yards from their RB1 and RB2 positions.',
    5: '*Dead Weight* - Lowest scoring starting player in a win.',
    6: '*The Atlanta Falcons Blew a 28-3 Lead in the Third Quarter* - Highest scoring losing team.',
    7: '*Nailed It* - The team that scores closest to its projected point total (over or under).',
    8: '*The Art of Losing* - Largest margin of loss.',
    9: '*Photo Finish* - Smallest margin of victory.',
    10: '*Full Send* - Starting QB with the longest passing TD.',
    11: '*You Got Mossed* - Team with the most WR receptions (WR1 and WR2 only).',
    12: '*So Close, But So Far* - Closest margin of loss.',
    13: '*Veteran Rest* - Highest scoring non-QB player on the bench.',
    14: '*Playoff Run* - Highest overachieving performance over the projected total.',
    15: '*Defense Wins Championships* - Highest scoring defense.',
    16: '*Peyton Manning Award* - Most offensive touchdowns scored (starters only).'
}

# Some other things we need to know
close_num = 14
playoff_teams = 6

# Get the current state of the NFL
def get_nfl_state():
    state_url = "https://api.sleeper.app/v1/state/nfl"
    nfl_state = requests.get(state_url).json()
    current_week = nfl_state.get('display_week', 'N/A')
    cal_week = nfl_state.get('week', 'N/A')
    current_season = nfl_state.get('season', 'N/A')

    return current_week, cal_week, current_season

# Get rosters and their stats
def get_rosters(league_id):
    rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    rosters_response = requests.get(rosters_url)
    rosters_response.raise_for_status()
    rosters = rosters_response.json()

    roster_to_owner = {}

    for roster in rosters:
        roster_id = roster.get("roster_id")
        owner_id = roster.get("owner_id")
        wins = roster.get('settings', {}).get('wins')
        losses = roster.get('settings', {}).get('losses')
        pf = roster.get('settings', {}).get('fpts')
        if roster_id is not None and owner_id is not None:
            roster_to_owner[roster_id] = {"owner_id": owner_id, "wins": wins, "pf": pf, "losses": losses}

    return roster_to_owner

# Map rosters to team names
def get_owners(league_id):
    owners_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    owners_response = requests.get(owners_url)
    owners_response.raise_for_status()
    owners = owners_response.json()

    owner_to_team = {}

    for owner in owners:
        owner_id = owner.get("user_id")
        metadata = owner.get("metadata", {})
        owner_name = owner.get("display_name")
        team_name = metadata.get("team_name") or "NAME YOUR TEAM"
        if owner_name == "TitletownAttack" and team_name == "NAME YOUR TEAM":
            team_name = owner_name
        if owner_id is not None and team_name is not None:
            owner_to_team[owner_id] = {"team": team_name, "owner": owner_name}

    return owner_to_team

# Get Scoreboards - this is the key component
def get_scoreboard(league_id, week):
    roster_to_owner = get_rosters(league_id)
    owner_to_team = get_owners(league_id)
    matchups_url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    matchups_response = requests.get(matchups_url)
    matchups_response.raise_for_status()
    matchups = matchups_response.json()

    scoreboard = {}

    # Add roster and owner info to scoreboards from info in get_rosters() and get_owners()
    for matchup in matchups:
        matchup_id = matchup.get("matchup_id")
        roster_id = matchup.get("roster_id")
        points = matchup.get("points")
        owner_id = roster_to_owner[roster_id]["owner_id"]
        team_wins = roster_to_owner[roster_id]["wins"]
        team_losses = roster_to_owner[roster_id]["losses"]
        team_pf = roster_to_owner[roster_id]["pf"]
        team_name = owner_to_team[owner_id]["team"]
        owner_name = owner_to_team[owner_id]["owner"]

        if matchup_id not in scoreboard:
            scoreboard[matchup_id] = {"team1": None, "team2": None}
            team = "team1"
            
        else:
            team = "team2"

        scoreboard[matchup_id][team] = {
            "owner": owner_name,
            "name": team_name,
            "points": points,
            "wins": team_wins,
            "losses": team_losses,
            "pf": team_pf,
        }

    return scoreboard

# task thursday-matchups
def get_matchups(league_id, week, which_league):
    scoreboard = get_scoreboard(league_id, week)
    matchup_message = "___________________________________________________________________________\n"
    matchup_message += f"🏈 *{which_league} - Matchups for Week {week}:* 🏈\n\n"

    for i, matchup_id in enumerate(scoreboard):
        matchup = scoreboard[matchup_id]

        matchup_message += f"• *{matchup['team1']['name']}* ({matchup['team1']['owner']}) - vs. - *{matchup['team2']['name']}* ({matchup['team2']['owner']})\n\n"

    return matchup_message

# task weekly-challenge
def get_weekly_challenge(week):
    challenge = weekly_challenge[week]
    challenge_message = f"🏈  🏈  Welcome to Week {week}! This week's challenge: {challenge}  🏈  🏈"
    return challenge_message

# task friday-scores
def get_scores(league_id, week, which_league, event):
    scoreboard = get_scoreboard(league_id, week)
    scoreboard_message = "___________________________________________________________________________\n"
    scoreboard_message += f"🏈  *{which_league} - {event}!*  🏈\n\n"

    for i, matchup_id in enumerate(scoreboard):
        matchup = scoreboard[matchup_id]
        scoreboard_message += (
            f"{matchup['team1']['name']} ({matchup['team1']['owner']})   {matchup['team1']['points']:.2f}\n"
            f"{matchup['team2']['name']} ({matchup['team2']['owner']})   {matchup['team2']['points']:.2f}\n\n\n"
        )

    return scoreboard_message

# task final-scores
def get_final_scores(league_id, week, which_league):
    scoreboard = get_scoreboard(league_id, week)

    scoreboard_message = "___________________________________________________________________________\n"
    scoreboard_message += f"🏈  *{which_league} - Final scores for week {week}!*  🏈\n\n"

    for i, matchup_id in enumerate(scoreboard):
        matchup = scoreboard[matchup_id]
        first_score = matchup['team1']['points']
        second_score = matchup['team2']['points']

        if first_score > second_score:
            scoreboard_message += (
                f"*{matchup['team1']['name']} ({matchup['team1']['owner']})   {first_score:.2f}*\n"
                f"{matchup['team2']['name']} ({matchup['team2']['owner']})   {second_score:.2f}\n\n\n"
            )
        elif second_score > first_score:
            scoreboard_message += (
                f"{matchup['team1']['name']} ({matchup['team1']['owner']})   {first_score:.2f}\n"
                f"*{matchup['team2']['name']} ({matchup['team2']['owner']})   {second_score:.2f}*\n\n\n"
            )
        else:
            scoreboard_message += (
                f"{matchup['team1']['name']} ({matchup['team1']['owner']})   {first_score:.2f}\n"
                f"{matchup['team2']['name']} ({matchup['team2']['owner']})   {second_score:.2f}\n\n\n"
            )
    
    return scoreboard_message

# task close-games
def get_close_games(league_id, week, which_league):
    scoreboard = get_scoreboard(league_id, week)

    close_game_message = "___________________________________________________________________________\n"
    close_game_message += f"🚨 😰  *{which_league} - Close games*  😰 🚨\n\n"
    close_count = 0

    for i, matchup_id in enumerate(scoreboard):
        matchup = scoreboard[matchup_id]
        first_score = matchup['team1']['points']
        second_score = matchup['team2']['points']

        difference = round(abs(first_score - second_score),2)

        if difference < close_num:
            close_game_message += (
                f"{matchup['team1']['name']}   {first_score:<8.2f}\n"
                f"{matchup['team2']['name']}   {second_score:<8.2f}\n"
                f"{'*Point differential:'}   {difference:<8.2f}*\n\n\n"
            )
            close_count += 1
    
    if close_count > 0:
        return close_game_message

# task standings
def standings_update(league_id, week, which_league):
    scoreboard = get_scoreboard(league_id, week)

    standings_message = "___________________________________________________________________________\n"
    standings_message += f"🏈  🏈  *{which_league} - Current Standings*  🏈  🏈\n\n"

    team_stats = []

    for matchup in scoreboard.values():
        for team_data in matchup.values():
            owner = team_data.get('owner')
            name = team_data.get('name')
            wins = team_data.get('wins')
            losses = team_data.get('losses')
            pf = team_data.get('pf')
            team_stats.append((owner, name, wins, losses, pf))

    standings = sorted(team_stats, key=lambda x: (x[2], x[4]), reverse=True)

    try:
        playoff_line = playoff_teams - 1
    except:
        playoff_line = 5
    for i, team in enumerate(standings):
        owner, name, wins, losses, pf = team
        standings_message += f"*{i+1}. {name}* ({owner}) ..... *{wins}-{losses}*\n"
        if i == playoff_line:
            standings_message += "________________________________\n\n"

    return standings_message

# Post to Slack app via incoming webhook
def post_to_slack_webhook(message):
    """Posts a message to Slack using an incoming webhook."""

    if not WEBHOOK_URL:
        print("Error: Slack webhook URL is not set.")
        return

    # The payload is a dictionary that will be converted to JSON
    # 'text' is the simplest way to send a message
    payload = {
        "text": message
    }

    headers = {
        "Content-type": "application/json"
    }

    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an HTTPError if the status is 4xx or 5xx
        print("✅ Message posted successfully via incoming webhook!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting message to Slack: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', help='The task to perform')
    parser.add_argument('--league', help='The ID of the league to process')
    args = parser.parse_args()

    league_info = leagues[args.league]

    current_week, cal_week, current_season = get_nfl_state()

    match args.task:
        case 'thursday-matchups':
            output = get_matchups(league_info["id"], current_week, league_info["name"])
            post_to_slack_webhook(output)

        case 'weekly-challenge':
            if current_week < 17:
                output = get_weekly_challenge(cal_week)
                post_to_slack_webhook(output)

        case 'friday-scores':
            output = get_scores(league_info["id"], current_week, league_info["name"], "Friday morning score update")
            post_to_slack_webhook(output)

        case 'close-games':
            output = get_close_games(league_info["id"], current_week, league_info["name"])
            post_to_slack_webhook(output)

        case 'monday-scores':
            output = get_scores(league_info["id"], current_week, league_info["name"], "Monday morning score update")
            post_to_slack_webhook(output)

        case 'final-scores':
            output = get_final_scores(league_info["id"], current_week, league_info["name"])
            post_to_slack_webhook(output)

        case 'standings':
            output = standings_update(league_info["id"], current_week, league_info["name"])
            post_to_slack_webhook(output)

        case _:
            print(f"Error: Unrecognized task '{args.task}'.")
            sys.exit(1)
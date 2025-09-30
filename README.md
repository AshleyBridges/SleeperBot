# SleeperBot

This utilizes the [Sleeper API](https://docs.sleeper.com/) to pull information from Sleeper Fantasy Football leagues and share via Slackbot, to keep players engaged all season long!

Can be run on a PC with scheduled tasks set to execute a .bat file. Sample .bat file included. 
Invoke via command line with python domino_sleeperbot.py --task \<taskname\> --league \<leagueid\>

## Current Schedule
- Wednesday:
     - 9am PT: Weekly Challenge
- Thursday:
     - 8am PT: Weekly Matchups
- Friday:
     - 8am PT: Score Updates
- Monday: 
     - 8am PT: Score Updates
     - 11am PT: Close Games
- Tuesday: 
     - 8am PT: Final Scores
     - 9am PT: Updated League Standings
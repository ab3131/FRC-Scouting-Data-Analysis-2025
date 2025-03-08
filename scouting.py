import tba
import gle
import json
import re
import logging, coloredlogs, verboselogs
import argparse
import statbotics

parser = argparse.ArgumentParser(description="Scouting Program")
parser.add_argument('-l', '--level', type=str, choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 
					'NOTICE', 'SUCCESS', 'SPAM', 'VERBOSE', 'NOTSET'], default='CRITICAL', help="Set the logging level")
args = parser.parse_args()
level = args.level


coloredlogs.install(fmt='%(asctime)s.%(msecs)03d [%(process)d] %(levelname)s %(message)s', level=f'{level}')
verboselogs.install()
l = logging.getLogger('__name__')
gle.init(l)
sb = statbotics.Statbotics()

def get_match_name(match_code, loggger):
	l.verbose(f"Decoding Match Name: {match_code}")
	match_types = {
		"qm": "Qualification Match ",
		"qf": "Quarterfinals ",
		"sf": "Semifinals ",
		"f": "Finals ",
		"m": " Match "
	}
	split = re.findall(r'\d+|\D+', match_code)
	output = ""
	for elem in split:
		if elem in match_types:
			output += match_types[elem]
		else:
			output += elem

	l.notice(f"Got Match Name: {output}")
	return output

def parse_rank_and_assign_color(team_info):
	if team_info=="":
		return "#bbbbbb"
	try:
		rank_part = team_info.split("Rank")[1].split("with")[0].strip()
		rank, total_teams = map(int, rank_part.split('/'))
		ratio = (rank - 1) / (total_teams - 1)

		if ratio < 0.5:
			red = int(255 * 2 * ratio)
			green = 255
		else:
			red = 255
			green = int(255 * (1 - 2 * (ratio - 0.5)))

		blue = 0
		color = f"#{red:02x}{green:02x}{blue:02x}"

		return color

	except:
		return "#bbbbbb"

def remove_substrings(input_string):
	substrings = ["<b>", "</b>"]
	for substring in substrings:
		input_string = input_string.replace(substring, "")
	return input_string


def find_top_teams(alliances):
    # Initialize a dictionary to store the result with empty strings for each team
    result = {0: {team_id: "" for team_id in alliances[0]}, 1: {team_id: "" for team_id in alliances[1]}}
    
    # Initialize placeholders for highest CCWM and OPR, and lowest DPR
    performance_metrics = {
        'ccwm': {'0': {'value': float('-inf'), 'team': ''}, '1': {'value': float('-inf'), 'team': ''}},
        'opr': {'0': {'value': float('-inf'), 'team': ''}, '1': {'value': float('-inf'), 'team': ''}},
        'dpr': {'0': {'value': float('inf'), 'team': ''}, '1': {'value': float('inf'), 'team': ''}}
    }

    # Iterate through each alliance and team to find the top performers
    for alliance, teams in alliances.items():
        for team_id, metrics in teams.items():
            for metric, value in metrics.items():
                value_float = float(value)
                if metric == 'dpr':
                    # For DPR, lower is better
                    if value_float < performance_metrics[metric][str(alliance)]['value']:
                        performance_metrics[metric][str(alliance)]['value'] = value_float
                        performance_metrics[metric][str(alliance)]['team'] = team_id
                else:
                    # For CCWM and OPR, higher is better
                    if value_float > performance_metrics[metric][str(alliance)]['value']:
                        performance_metrics[metric][str(alliance)]['value'] = value_float
                        performance_metrics[metric][str(alliance)]['team'] = team_id

    # Assign the letters to the teams based on their leading performance
    for metric, alliances in performance_metrics.items():
        for alliance, info in alliances.items():
            if info['team']:  # Check if a team has been assigned as a top performer
                letter = metric[0].upper()
                result[int(alliance)][info['team']] += letter

    return result

def parse_scouting_data(row):
	output = ""
	output += ("Auto: "+row[3]+"\n")
	output += ("Coral Levels: "+ row[4] + "\n")
	algaestring = ""
	if "Mechanism to score in processor" in row[5]:
		algaestring+="processor, "
	if "Mechanism to score in barge" in row[5]:
		algaestring+="barge"
	output += ("Algae: "+ algaestring + "\n")
	output += ("Climb: "+row[6] + "\n")
	output += ("Intake: "+row[7]+"\n")
	output += ("Algae Removal: "+row[8]+"\n")
	return output


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="A program that collects data on the performance of high school robotics teams and outputs the data formatted onto a presentation"
	)
	parser.add_argument("-log", required=False, choices=['CRITICAL','ERROR','SUCCESS','WARNING','NOTICE','INFO','VERBOSE','DEBUG','SPAM'], default='SUCCESS')
	args = parser.parse_args()
	level = args.log

tba_api_key = tba.access_storage("tba_api_key", l)
year = tba.access_storage("year", l)
event_code = tba.access_storage("event_code", l)
match_code = input("Match Code: ")
comp_code = year+event_code


match_info = tba.get_match_info(year, event_code, match_code, l)
match_teams = [[team[3:] for team in sublist] for sublist in [match_info["alliances"]["blue"]["team_keys"], match_info["alliances"]["red"]["team_keys"]]]
team_info = []

team_info = [[tba.get_team_status(year, team, l) for team in alliance] for alliance in match_teams]
sb_stats = sb.get_match(comp_code+"_"+match_code)

team_types = {0: "bt", 1: "rt"}

#print(sb_stats["epa_win_prob"])
#print(sb_stats["epa_winner"])

REPLACE_WORDS = {
	"{regional_name}": tba.get_event_name(comp_code, l),
	"{match_name}": get_match_name(match_code, l),
	"{tba_p_rt}": str(round(100-(100*tba.get_match_pred(comp_code, match_code, "red", l)), 2)),
	"{tba_p_bt}": str(round(100*tba.get_match_pred(comp_code, match_code, "blue", l), 2)),
#	"{sb_p_rt}": str(round(100*sb_stats["epa_win_prob"], 2)),
#	"{sb_p_bt}": str(round((100 - (100*sb_stats["epa_win_prob"])), 2)),
#	"{epa_rt}": str(sb_stats["red_epa_sum"]),
#	"{epa_bt}": str(sb_stats["blue_epa_sum"])

}

REPLACE_COLORS = {}
REPLACE_IMAGES = {}

"""
a: alliance
t: team
k: key
i: info

"""

penguin = {0: {}, 1: {}}

second_pass = False

for a in range(2):
	total_opr = 0.0
	total_dpr = 0.0

	for t in range(3):
		k = team_types[a]
		team = match_teams[a][t]
		i = team_info[a][t]

		REPLACE_WORDS[f"{{{k}{t+1}}}"] = team
		REPLACE_WORDS[f"{{{k}{t+1}_name}}"] = tba.get_team_name(team, l)
		REPLACE_WORDS[f"{{{k}{t+1}_prev_regional}}"] = tba.get_event_name(tba.prev_comp(comp_code, team, l), l)
		REPLACE_WORDS[f"{{{k}{t+1}_prev_ccwm}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team, l), team, l)["ccwm"]
		REPLACE_WORDS[f"{{{k}{t+1}_prev_opr}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team, l), team, l)["opr"]
		REPLACE_WORDS[f"{{{k}{t+1}_prev_dpr}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team, l), team, l)["dpr"]


		ccwm = tba.get_team_stats(comp_code, team, l)["ccwm"]
		opr = tba.get_team_stats(comp_code, team, l)["opr"]
		total_opr += float(opr)
		dpr = tba.get_team_stats(comp_code, team, l)["dpr"]
		total_dpr += float(dpr)

		penguin[a][team] = {"opr": opr, "dpr": dpr, "ccwm": ccwm}

		REPLACE_WORDS[f"{{{k}{t+1}_curr_ccwm}}"] = ccwm
		REPLACE_WORDS[f"{{{k}{t+1}_curr_opr}}"] = opr
		REPLACE_WORDS[f"{{{k}{t+1}_curr_dpr}}"] = dpr

		REPLACE_WORDS[f"{{{k}{t+1}_prev_status}}"] = remove_substrings(i[tba.prev_comp(comp_code, team, l)]["overall_status_str"]) if tba.prev_comp(comp_code, team, l) != None else ""
		REPLACE_WORDS[f"{{{k}{t+1}_curr_status}}"] = remove_substrings(i[comp_code]["overall_status_str"])

	if second_pass:
		REPLACE_WORDS["{opr_rt}"] = str(round(total_opr, 2))
		REPLACE_WORDS["{dpr_bt}"] = str(round(total_dpr, 2))
	else:
		REPLACE_WORDS["{opr_bt}"] = str(round(total_opr, 2))
		REPLACE_WORDS["{dpr_rt}"] = str(round(total_dpr, 2))
	second_pass = True

result = find_top_teams(penguin)
print(result)

for a in range(2):
	for t in range(3):
		k = team_types[a]
		team = match_teams[a][t]
		i = team_info[a][t]

		REPLACE_WORDS[f"{{{k}{t+1}_COD}}"] = result[a][team]



for a in range(2):
	for t in range(3):
		k = team_types[a]
		team = match_teams[a][t]
		i = team_info[a][t]
		color = parse_rank_and_assign_color(remove_substrings(i[comp_code]["overall_status_str"]))
		REPLACE_COLORS[f"{{{k}{t+1}}}"] = color
		REPLACE_COLORS[f"{{{k}{t+1}_curr_status}}"] = color

		color = parse_rank_and_assign_color(remove_substrings(remove_substrings(i[tba.prev_comp(comp_code, team, l)]["overall_status_str"]) if tba.prev_comp(comp_code, team, l) != None else ""))
		REPLACE_COLORS[f"{{{k}{t+1}_prev_status}}"] = color
		REPLACE_COLORS[f"{{{k}{t+1}_name}}"] = "#ffffff"

data = gle.get_sheet_data(l)

for a in range(2):
	for t in range(3):
		k = team_types[a]
		team = match_teams[a][t]
		row = gle.sheets_lookup(team, data, l)
		print(team, row)
		if (row != None):
			REPLACE_IMAGES[f"{{{k}{t+1}_photo}}"] = row[9]
			REPLACE_WORDS[f"{{{k}{t+1}_scouting}}"] = parse_scouting_data(row)
			print(parse_scouting_data(row))
			REPLACE_WORDS[f"{{{k}{t + 1}_coral}}"] = row[4]
			REPLACE_WORDS[f"{{{k}{t + 1}_climb}}"] = row[6]

pres = gle.copy_presentation("1kYfFspMuULX_o9jot3aGFUaUEY8-ae8bzlEk3KCMfhU", get_match_name(match_code, l), l)
response = gle.update_textbox_backgrounds(pres, REPLACE_COLORS, l)
response = gle.replace_all_text_in_slides(pres, REPLACE_WORDS, l)

response = gle.replace_text_with_images(pres, REPLACE_IMAGES, l)
print(response)


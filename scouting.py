import tba
import gle
import json
import re
import logging, coloredlogs, verboselogs

coloredlogs.install(fmt='%(asctime)s,%(msecs)03d [%(process)d] %(levelname)s %(message)s', level='SUCCESS')
verboselogs.install()
logger = logging.getLogger('__name__')


tba_api_key = tba.access_storage("tba_api_key")
year = tba.access_storage("year")
event_code = tba.access_storage("event_code")
match_code = input("Match Code: ")
comp_code = year+event_code


match_info = tba.get_match_info(year, event_code, match_code)
match_teams = [[team[3:] for team in sublist] for sublist in [match_info["alliances"]["blue"]["team_keys"], match_info["alliances"]["red"]["team_keys"]]]
team_info = []

team_info = [[tba.get_team_status(year, team) for team in alliance] for alliance in match_teams]


def get_match_name(match_code):
	logger.verbose(f"Decoding Match Name: {match_code}")
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

	logger.notice(f"Got Match Name: {output}")
	return output

def remove_substrings(input_string):
	substrings = ["<b>", "</b>"]
	for substring in substrings:
		input_string = input_string.replace(substring, "")
	return input_string


team_types = {0: "bt", 1: "rt"}
REPLACE_WORDS = {
	"{regional_name}": tba.get_event_name(comp_code),
	"{match_name}": get_match_name(match_code),
	"{p_rt}": str(round(100-(100*tba.get_match_pred(comp_code, match_code, "red")), 2)),
	"{p_bt}": str(round(100*tba.get_match_pred(comp_code, match_code, "blue"), 2))
}


"""
a: alliance
t: team
k: key
i: info

"""

for a in range(2):
	for t in range(3):
		k = team_types[a]
		team = match_teams[a][t]
		i = team_info[a][t]

		REPLACE_WORDS[f"{{{k}{t+1}}}"] = team
		REPLACE_WORDS[f"{{{k}{t+1}_name}}"] = tba.get_team_name(team)
		REPLACE_WORDS[f"{{{k}{t+1}_prev_regional}}"] = tba.get_event_name(tba.prev_comp(comp_code, team))
		REPLACE_WORDS[f"{{{k}{t+1}_prev_ccwm}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team), team)["ccwm"]
		REPLACE_WORDS[f"{{{k}{t+1}_prev_opr}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team), team)["opr"]
		REPLACE_WORDS[f"{{{k}{t+1}_prev_dpr}}"] = tba.get_team_stats(tba.prev_comp(comp_code, team), team)["dpr"]
		REPLACE_WORDS[f"{{{k}{t+1}_curr_ccwm}}"] = tba.get_team_stats(comp_code, team)["ccwm"]
		REPLACE_WORDS[f"{{{k}{t+1}_curr_opr}}"] = tba.get_team_stats(comp_code, team)["opr"]
		REPLACE_WORDS[f"{{{k}{t+1}_curr_dpr}}"] = tba.get_team_stats(comp_code, team)["dpr"]
		REPLACE_WORDS[f"{{{k}{t+1}_prev_status}}"] = remove_substrings(i[tba.prev_comp(comp_code, team)]["overall_status_str"])
		REPLACE_WORDS[f"{{{k}{t+1}_curr_status}}"] = remove_substrings(i[comp_code]["overall_status_str"])




REPLACE_COLORS = {
	"{match_name}": "#ffff00"
}

gle.init()
pres = gle.copy_presentation("1kyycROakSpSXfv_8ehGT-h0zobi4dCWItsX4zk50Dm4", get_match_name(match_code))
response = gle.update_textbox_backgrounds(pres, REPLACE_COLORS)
response = gle.replace_all_text_in_slides(pres, REPLACE_WORDS)


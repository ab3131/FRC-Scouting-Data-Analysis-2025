import json
import requests
import datetime
import logging, coloredlogs, verboselogs

coloredlogs.install(fmt="%(asctime)s,%(msecs)03d [%(levelname)s] %(message)s", level='DEBUG')
verboselogs.install()
logger = logging.getLogger('__name__')

# Define the name of the JSON file
file_name = "config.json"
cache = {}  # Initialize an empty cache

def access_storage(key):
	logger.verbose(f"Accessing config.json for {key}")
	try:
		# Open the JSON file for reading
		with open(file_name, "r") as json_file:
			# Load the JSON data from the file
			data = json.load(json_file)
			# Check if the key exists in the JSON data
			if key in data:
				# Extract and print the value associated with the key
				value = data[key]
				logger.notice(f"Access successful {key}: {value}")
				return(value)
			else:
				logger.critical(f"The key '{key}' does not exist in the JSON file.")

	except FileNotFoundError:
		logger.critical(f"File '{file_name}' not found.")
	except json.JSONDecodeError:
		logger.critical(f"Error decoding JSON in '{file_name}'.")



"""###################################################################################################
The Blue Alliance API Call #1: Match Information

This program begins by taking the year and match number and requesting information from the server to
get a sense for the match that is going to be played
###################################################################################################"""


def get_match_info(year, event_code, match):
	logger.info(f"[TBA] Requesting match info for {year}{event_code}_{match}")
	data = make_request(f"match/{year}{event_code}_{match}/simple")
	logger.debug("JSON Response")
	logger.debug(json.dumps(data, indent=2))
	return data


"""###################################################################################################
The Blue Alliance API Call #2: Team Information

This program continues by doing a deep dive into each team, exploring all the competition data on 
them for the season. The Blue Alliance API will give us all the data, but we only care about the last
competition they competed in and the current competition. 
###################################################################################################"""


def get_team_name(team_num):
	logger.info(f"[TBA] Requesting team name for {team_num}")
	data = make_request(f"team/frc{team_num}/simple")
	logger.debug("JSON Response")
	logger.debug(json.dumps(data, indent=2))
	return data["nickname"]

def get_team_status(year, team_num):
	logger.info(f"[TBA] Requesting team status for {team_num}")
	data = make_request(f"team/frc{team_num}/events/{year}/statuses")
	logger.debug("JSON Response")
	logger.debug(json.dumps(data, indent=2))
	return data

def get_match_pred(comp_code, match_code, alliance):
	logger.info(f"[TBA] Requesting match prediction for {match_code}")
	data = make_request(f"event/{comp_code}/predictions")
	logger.debug("JSON Response")
	logger.debug(json.dumps(data, indent=2))

	if (match_code.startswith("qm")):
		return data["match_predictions"]["qual"][comp_code+"_"+match_code]["prob"]
	return data["match_predictions"]["playoff"][comp_code+"_"+match_code]["prob"]

def get_event_name(comp_code):
	logger.info(f"[TBA] Requesting event name for {comp_code}")
	if comp_code == None:
		logger.warning("No competition found, labeling name as None")
		return "No Competition"

	data = make_request(f"event/{comp_code}/simple")["name"]
	logger.debug("JSON Response")
	logger.debug(json.dumps(data, indent=2))
	return data

def get_team_stats(comp_code, team_num):
	global cache

	logger.info(f"[TBA] Requesting team stats for {team_num}")
	if comp_code == None:
		logger.warning("No competition found, labeling stats as None")
		return {"ccwm": "None", "opr":"None", "dpr":"None"}

	if comp_code in cache and f"frc{team_num}" in cache[comp_code]:
		data = cache[comp_code]
	else:
		data = make_request(f"event/{comp_code}/oprs")
		logger.debug("JSON Output")
		logger.debug("\n"+json.dumps(data, indent=2))
		cache[comp_code] = data

	stats = {
		"opr": str(round(data["oprs"][f"frc{team_num}"], 2)),
		"dpr": str(round(data["dprs"][f"frc{team_num}"], 2)),
		"ccwm": str(round(data["ccwms"][f"frc{team_num}"], 2))
	}
	return stats

def prev_comp(comp_code, team_num):
	logger.info(f"[TBA] Requesting competition prior to {comp_code} for {team_num}")
	year = comp_code[0:4]
	events = make_request(f"team/frc{team_num}/events/{year}/simple")
	logger.debug("JSON Output")
	logger.debug("\n"+json.dumps(events, indent=2))
	sorted_events = sorted(events, key=lambda x: x['start_date'])
	comps =  [event['key'] for event in sorted_events]
	for index, event in enumerate(comps):
		if event == comp_code:
			if index > 0:
				return sorted_events[index - 1]['key']
			else:
				return None
	return None
		

def make_request(subpage):
	url = "https://www.thebluealliance.com/api/v3/"+subpage
	tba_api_key = access_storage("tba_api_key")
	# Define the headers, including the API key
	headers = {
		"accept": "application/json",
		"X-TBA-Auth-Key": tba_api_key
	}

	try:
		# Make the GET request
		response = requests.get(url, headers=headers)

		# Check if the request was successful (HTTP status code 200)
		if response.status_code == 200:
			# Parse the JSON response
			data = response.json()
			logger.success(f"API request {subpage} succeeded with status code {response.status_code}")
			return data
		else:
			logger.error(f"API request {subpage} failed with status code {response.status_code}")
			return None

	except requests.exceptions.RequestException as e:
		logger.error(f"API request {subpage} failed with error {e}")
		return None



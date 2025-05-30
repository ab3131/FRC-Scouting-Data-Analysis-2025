from flask import Flask, request, jsonify
from flask_cors import CORS
import tba
import gle
import re
import logging, coloredlogs, verboselogs
import statbotics
import cohere
import os

app = Flask(__name__)
CORS(app)

coloredlogs.install(fmt='%(asctime)s.%(msecs)03d [%(process)d] %(levelname)s %(message)s', level='INFO')
verboselogs.install()
l = logging.getLogger(__name__)
gle.init(l)
sb = statbotics.Statbotics()

cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

def get_match_name(match_code):
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
    return output

def remove_substrings(input_string):
    substrings = ["<b>", "</b>"]
    for substring in substrings:
        input_string = input_string.replace(substring, "")
    return input_string

def parse_scouting_data(row):
    output = ""
    output += ("Auto: " + row[3] + "\n")
    output += ("Coral Levels: " + row[4] + "\n")
    algaestring = ""
    if "Mechanism to score in processor" in row[5]:
        algaestring += "processor, "
    if "Mechanism to score in barge" in row[5]:
        algaestring += "barge"
    output += ("Algae: " + algaestring + "\n")
    output += ("Climb: " + row[6] + "\n")
    output += ("Intake: " + row[7] + "\n")
    output += ("Algae Removal: " + row[8] + "\n")
    return output

def get_match_report(match_code):
    tba_api_key = tba.access_storage("tba_api_key", l)
    year = tba.access_storage("year", l)
    event_code = tba.access_storage("event_code", l)
    comp_code = year + event_code

    match_info = tba.get_match_info(year, event_code, match_code, l)
    match_teams = [[team[3:] for team in sublist] for sublist in
                   [match_info["alliances"]["blue"]["team_keys"], match_info["alliances"]["red"]["team_keys"]]]
    team_info = [[tba.get_team_status(year, team, l) for team in alliance] for alliance in match_teams]

    sb_stats = sb.get_match(comp_code + "_" + match_code)

    data = gle.get_sheet_data(l)

    report = {
        "match_name": get_match_name(match_code),
        "event_name": tba.get_event_name(comp_code, l),
        "red": [],
        "blue": [],
        "capabilities": {"red": {}, "blue": {}},
        "win_probabilities": {
            "event": tba.get_event_name(comp_code, l),
            "match": get_match_name(match_code),
            "tba_red": str(round(100 - (100 * tba.get_match_pred(comp_code, match_code, "red", l)), 2)),
            "tba_blue": str(round(100 * tba.get_match_pred(comp_code, match_code, "blue", l), 2)),
            "sb_red": str(round(100 * sb_stats["pred"]["red_win_prob"], 2)),
            "sb_blue": str(round((100 - (100 * sb_stats["pred"]["red_win_prob"])), 2)),
            "epa_red": str(sb_stats["pred"]["red_score"]),
            "epa_blue": str(sb_stats["pred"]["blue_score"])
        }
    }

    for a, color in enumerate(["blue", "red"]):
        coral_list = []
        algae_list = []
        climb_list = []

        for team in match_teams[a]:
            row = gle.sheets_lookup(team, data, l)
            scouting = parse_scouting_data(row) if row else "No data"
            report[color].append({"id": team, "summary": scouting})

            if row:
                coral = row[4] if row[4] else ""
                coral_list.append(coral)
                climb = row[6] if row[6] else ""
                climb_list.append(climb)
                algae = ""
                if "Mechanism to score in processor" in row[5]:
                    algae += "Mechanism to score in processor, "
                if "Mechanism to score in barge" in row[5]:
                    algae += "Mechanism to score in barge"
                algae_list.append(algae.strip())
            else:
                coral_list.append("")
                climb_list.append("")
                algae_list.append("")

        report["capabilities"][color]["coral"] = ";".join(coral_list)
        report["capabilities"][color]["algae"] = ";".join(algae_list)
        report["capabilities"][color]["climb"] = ";".join(climb_list)

    return report

@app.route('/api/match', methods=['POST'])
def match_info():
    data = request.json
    match_code = data.get('match_code')
    try:
        report = get_match_report(match_code)
        return jsonify({"success": True, "data": report})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/strategy-summary', methods=['POST'])
def strategy_summary():
    try:
        body = request.json
        red_summaries = body.get("red", [])
        blue_summaries = body.get("blue", [])

        prompt = f"""
        Analyze the following scouting summaries for two alliances in an FRC robotics match. Provide 2-3 short strategic takeaways or observations.

        Red Alliance:
        {'\n'.join(red_summaries)}

        Blue Alliance:
        {'\n'.join(blue_summaries)}

        Provide clear, concise bullet points. Go directly into the bullet points, there should be NO TEXT prior to your observations. When referencing certain capabilities, YOU MUST provide team numbers to reference. These team numbers SHOULD NEVER be in list format. Each Team number should ALWAYS have \"Team\" before it. There should be no \"Team 1, 2...\" or \"Team 1 and 2\"...these are completely off limits. Always reference them as 'Team 1, Team 2' etc.
        """

        response = cohere_client.generate(
            model='command-r-plus',
            prompt=prompt,
            max_tokens=150,
            temperature=0.7
        )

        summary = response.generations[0].text.strip()
        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        print("Cohere error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5050)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import tba
import gle
import re
import logging, coloredlogs, verboselogs
import statbotics
import cohere
import os
import requests
from io import BytesIO
from flask import send_file

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=os.path.join(basedir, 'scoutingweb', 'build'), static_url_path='/')
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
    print(sb_stats)

    data = gle.get_sheet_data(l)
    print(tba.get_match_pred(comp_code, match_code, "red", l))
    report = {
        "match_name": get_match_name(match_code),
        "event_name": tba.get_event_name(comp_code, l),
        "red": [],
        "blue": [],
        "capabilities": {"red": {}, "blue": {}},
        "win_probabilities": {
            "event": tba.get_event_name(comp_code, l),
            "match": get_match_name(match_code),
            "tba_red": str(round((100 * tba.get_match_pred(comp_code, match_code, "red", l)), 2)),
            "tba_blue": str(round((100 * tba.get_match_pred(comp_code, match_code, "blue", l)), 2)),
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

"""
@app.route('/api/strategy-summary', methods=['POST'])
def strategy_summary():
    try:
        body = request.json
        red_summaries = body.get("red", [])
        blue_summaries = body.get("blue", [])

        prompt = f
        Analyze the following scouting summaries for two alliances in an FRC robotics match. Provide 2-3 short strategic takeaways or observations.

        Red Alliance:
        {'\n'.join(red_summaries)}

        Blue Alliance:
        {'\n'.join(blue_summaries)}

        Provide clear, concise bullet points. Go directly into the bullet points, there should be NO TEXT prior to your observations. When referencing certain capabilities, YOU MUST provide team numbers to reference. These team numbers SHOULD NEVER be in list format. Each Team number should ALWAYS have \"Team\" before it. There should be no \"Team 1, 2...\" or \"Team 1 and 2\"...these are completely off limits. Always reference them as 'Team 1, Team 2' etc.
        

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
"""

@app.route('/api/curryear', methods=['GET'])
def current_year():
    return tba.get_year(l)

def convert_drive_link(link):
    # Match both /file/d/FILE_ID/ and ?id=FILE_ID patterns
    match = re.search(r'(?:/d/|id=)([a-zA-Z0-9_-]+)', link)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return link
@app.route('/api/team-photo/<team_id>', methods=['GET'])
def get_team_photo(team_id):
    try:
        data = gle.get_sheet_data(l)
        row = gle.sheets_lookup(team_id, data, l)
        if row and len(row) > 9:
            raw_link = row[9]
            fixed_link = convert_drive_link(raw_link)
            return jsonify({"success": True, "photo_url": fixed_link})
        else:
            return jsonify({"success": False, "error": "No photo found for this team"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/photo-proxy/<team_id>', methods=['GET'])
def photo_proxy(team_id):
    try:
        data = gle.get_sheet_data(l)
        row = gle.sheets_lookup(team_id, data, l)
        if row and len(row) > 9:
            drive_link = row[9]
            file_id_match = re.search(r'(?:/d/|id=)([a-zA-Z0-9_-]+)', drive_link)
            if not file_id_match:
                return jsonify({"success": False, "error": "Invalid Google Drive link"}), 400

            file_id = file_id_match.group(1)
            proxy_url = f"https://drive.google.com/uc?export=view&id={file_id}"

            # Get the image bytes from the proxy_url
            headers = {'User-Agent': 'Mozilla/5.0'}  # Google blocks some bot-like requests
            img_res = requests.get(proxy_url, headers=headers)
            img_res.raise_for_status()

            return send_file(BytesIO(img_res.content), mimetype='image/jpeg')
        else:
            return jsonify({"success": False, "error": "No image"}), 404
    except Exception as e:
        l.exception("Image fetch failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/events/<int:year>', methods=['GET'])
def get_events(year):
    try:
        print(f"[DEBUG] Fetching events for year {year}")
        my_response = tba.obtain_events(year, l)

        if my_response is None:
            print("[ERROR] TBA response is None")
            return jsonify({'error': 'TBA returned None'}), 500

        print(f"[DEBUG] TBA response status code: {my_response.status_code}")
        if my_response.status_code != 200:
            return jsonify({'error': f'TBA error: {my_response.status_code}'}), 500

        events = my_response.json()
        print(f"[DEBUG] Retrieved {len(events)} events")
        return jsonify([
            {'key': e['key'], 'name': e['name']} for e in events
        ])

    except Exception as e:
        import traceback
        print("[EXCEPTION] Exception occurred in get_events:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/matches/<event_key>', methods=['GET'])
def get_matches(event_key):
    response = tba.obtain_matches(event_key, l)

    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch matches'}), 500

    matches = response.json()
    return jsonify([match['key'] for match in matches])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5050)

from __future__ import print_function
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools
import uuid
import ast


final_list = []
error_events = []

def parseTableForAlliances (table, event, amount):
	#table, title, teams
	final = []
	if (table == None):
		final = ['No Data', 'No Data', 'No Data', 'No Data', 'No Data', 'No Data', 'No Data', 'No Data', 'No Data']
	else:
		for rowindex in range(1,amount+1):
			row = table.find_all('tr')[rowindex]
			row = row.text.strip()
			row = row.replace("\n", "")
			row = row.split()
			items = [row[1],row[0],row[2],row[7],event]
			for elem in final_list:
				if elem[0]==items[0]:
					final_list.remove(elem)
			final_list.append(items)

def scouting_rating(text):
	rating = 0
	rating = 2+text.count("High")+text.count("Middle")+text.count("Low")+text.count("Cargo Ship")+text.count("Level 2 Starter")+text.count("1,2,3")+text.count("1,2")+text.count("1,3")
	if (rating>11):
		rating=11
	return rating

def scouting_color(color,text):
	if color=="red":
		values = [255,255,255,255,255,255,255,255,170,85,0]
		return values[scouting_rating(text)-1]/256
	if color=="green":
		values = [0,0,0,0,0,85,170,255,255,255,255]
		return values[scouting_rating(text)-1]/256
	if color=="blue":
		return 0

def prior_color(color,text):
	if color=="red":
		if text>2:
			return (abs(text-4))*0.5
		if text<=2:
			return 1
	if color=="green":
		if text<2:
			return text*0.5
		if text>=2:
			return 1
	if color=="blue":
		return 0
	

BACKGROUND_BRIGHTNESS = 0.5
SCOPES = (
	"https://www.googleapis.com/auth/spreadsheets.readonly",
	"https://www.googleapis.com/auth/presentations",
	"https://www.googleapis.com/auth/drive"
)

event_code = input("What competition are you attending? ")
if event_code == "1":
	print("Found: Sacramento Regional")
	event_code = "cada"
elif event_code == "2":
	print("Found: Silicon Valley Regional")
	event_code = "casj"
elif event_code == "test":
	print("Found: Cetral Valley Regional")
	event_code = "cafr"
else:
	print("Could not find competition. Autosetting to: Silicon Valley Regional")
	event_code = "casj"

match_number = input("Match Number: ")

head_page = "https://www.thebluealliance.com/event/2019"
"""
ranks = [[],[],[],[],[],[],[],[]]
error_events = []
try:
	print("Finding Event: "+event_code)
	quote_page = Request(head_page + event_code + "#results", headers={'User-Agent': 'Mozilla/5.0'})
	page = urlopen(quote_page)
	soup = BeautifulSoup(page, "html.parser")
	title = soup.find("h1", attrs={"itemprop": "summary"})
	title = title.text.strip()
	title = title[:-5]
	table = soup.find_all("table", attrs={"class": "match-table"})
	table = table[2]
	if (table==None):
		print("Skipped Event " + event_code + ": No Data Found")
		error_events.append(event_code)
		count +=1
		raise VoodooError("Well that sucks...")
	teams = table.find_all('tr')
	teams = table.find_all('a')
	teams = [str(a).split(">") for a in teams]
	teams = [b.pop(1) for b in teams]
	teams = [str(a).split("<") for a in teams]
	teams = [b.pop(0) for b in teams]
	teams = list(filter(None, teams))
	teams = [teams[n:n+7] for n in range(0, len(teams), 7)]
	teams = teams[1::2]
except Exception as e:
	print(e)

print(teams)
teams = [teams[int(match_number)-1][1],teams[int(match_number)-1][2],teams[int(match_number)-1][3],teams[int(match_number)-1][4],teams[int(match_number)-1][5],teams[int(match_number)-1][6]]
print(teams)
"""

teams = ["186","649","840","2367","2473","6241"]

try:
	print("Finding Event: "+event_code)
	website = "https://www.thebluealliance.com/event/2019" + event_code + "#rankings"
	quote_page = Request(website, headers={'User-Agent': 'Mozilla/5.0'})
	print(website)
	page = urlopen(quote_page)
	soup = BeautifulSoup(page, "html.parser")
	title = soup.find("h1", attrs={"itemprop": "summary"})
	title = title.text.strip()
	title = title[:-5]
	table = soup.find("table", attrs={"id": "rankingsTable"})
	if (table==None):
		print("Skipped Event " + event_code + ": No Data Found")
		error_events.append(event_code)
	numteams = table.find_all('tr')
	numteams = len(numteams)
	numteams -= 1
	print("Found "+str(numteams)+" teams")
	print("Copying information from "+title)
	parseTableForAlliances(table, title, numteams)
except Exception as e:
	print("Skipping Event "+event_code+" due to the following error:")
	print(e)
	error_events.append(event_code)


store = file.Storage("storage.json")
creds = store.get()
if not creds or creds.invalid:
	flow = client.flow_from_clientsecrets("client_secret.json", SCOPES)
	creds = tools.run_flow(flow, store)
HTTP = creds.authorize(Http())
SHEETS = discovery.build("sheets", "v4", http=HTTP)
SLIDES = discovery.build("slides", "v1", http=HTTP)
DRIVE = discovery.build("drive", "v3", http=HTTP)

print("Collecting data on The Blue Alliance")
f = open("output.txt","r")
team_data = f.read()
team_data = ast.literal_eval(team_data)

print("** Fetching Sheets data")
sheetID = "1IvRMs9ox8E6jViuN4iMW8GTkNJbH69FgfF-cPbah-Po"
orders = SHEETS.spreadsheets().values().get(range="Form Responses 1",
	spreadsheetId=sheetID).execute().get('values')

print("** Creating new slide deck")
matchTitle = event_code.upper()+" Q"+match_number+" Scouting Data"
DATA = {"title": matchTitle}
rsp = SLIDES.presentations().create(body=DATA).execute()
deckID = rsp['presentationId']
titleSlide = rsp["slides"][0]
titleID = titleSlide["pageElements"][0]["objectId"]
subtitleID = titleSlide['pageElements'][1]["objectId"]

print("** Creating slides & insert slide deck title+subtitle")
reqs = []
imagePageId = uuid.uuid4().hex
reqs.extend((
	{
		"createSlide": 
		{
	        "objectId": imagePageId,
	        "slideLayoutReference": 
	        {
	        	"predefinedLayout": "BLANK"
	        }
	    }
    },
    {
		"createImage": 
		{
			"url": "https://drive.google.com/a/sfhs.com/uc?id=1eB5ts9Gg1AQQ02Z5lk0ALAPjjqpN2HNF",
			"elementProperties": 
			{
				"pageObjectId": imagePageId,
				"size": 
				{
					"width": {"magnitude": 720, "unit": "PT"},
					"height": {"magnitude": 405, "unit": "PT"}
				},
				"transform": 
				{
					"scaleX": 1,
					"scaleY": 1,
					"translateX": 0,
					"translateY": 0,
					"unit": "PT"
				}
			}
		}
	}))
coordinates = [[625,240],[625,185],[625,130],[40,130],[40,185],[40,240]]
for elem in range(6):
	tempId = uuid.uuid4().hex
	reqs.extend((
	# INSERT TITLE TEXT
	{
        'createShape': 
        {
            'objectId': tempId,
            'shapeType': 'TEXT_BOX',
            'elementProperties': 
            {
                'pageObjectId': imagePageId,
                'size': 
                {
                    'height': {'magnitude': 50, 'unit': 'PT'},
                    'width': {'magnitude': 100, 'unit': 'PT'}
                },
                'transform': 
                {
                    'scaleX': 1,
                    'scaleY': 1,
                    'translateX': coordinates[elem][0],
                    'translateY': coordinates[elem][1],
                    'unit': 'PT'
                }
            }
        }
	},
	{
		"insertText": 
		{
			"objectId": tempId,
			"text": teams[elem],
		}
    },
    # FORMAT TITLE TEXT
    {
        'updateTextStyle': 
        {
            'objectId': tempId,
            'textRange': 
            {
                'type': 'ALL',
            },
            'style': 
            {
            	'backgroundColor':
            	{
            		'opaqueColor':
            		{
            			'rgbColor':
            			{
            				'red': 1,
            				'green': 1,
            				'blue': 1
            			}
            		}
            	},
                'fontFamily': 'Lato',
                'fontSize': 
                {
                    'magnitude': 18,
                    'unit': 'PT'
            	}
            },
            'fields': 'backgroundColor,fontFamily,fontSize'
        }
    }
	))
for team in teams:
	team_number = team
	for i in range(0,len(orders)-1):
		bodyText = "No Scouting Data"
		imageUrl = ""
		team_name = "No Team Name"
		if str(orders[i+1][2])==team:
			bodyText = "Sandstorm: "+orders[i+1][4]+"\n"+orders[i+1][5]+" Starter"+"\n"+"Hatch Panels: "+orders[i+1][6]+"\n"+"Cargo: "+orders[i+1][7]+"\n"+"Can end on Level "+orders[i+1][8]
			team_name = orders[i+1][3]
			if (len(orders[i+1])==11):
				imageUrl = "https://drive.google.com/uc?id="+((orders[i+1][10].split("="))[1])
			break
	#https://drive.google.com/a/sfhs.com/uc?id=1jS2dngfiOYwYTF8RfmiQCfnklcR2fg_s&export=download
	pageId = uuid.uuid4().hex
	titleId = uuid.uuid4().hex
	bodyId = uuid.uuid4().hex
	priorId = uuid.uuid4().hex
	currentId = uuid.uuid4().hex
	compId = uuid.uuid4().hex
	scoutingRatingId = uuid.uuid4().hex
	reqs.extend((
		# CREATES TEAM SLIDE AND TEXT BOX FOR TITLE TEXT
		{
			"createSlide": 
			{
		        "objectId": pageId,
		        "slideLayoutReference": 
		        {
		        	"predefinedLayout": "TITLE_ONLY"
		        },
		        "placeholderIdMappings": 
		        [
		        	{
		        		"layoutPlaceholder": 
		        		{
		           			"type": "TITLE",
		           			"index": 0
		           		},
		            	"objectId": titleId,
		        	},
		        ],
		    }
	    },
		# INSERT TITLE TEXT
		{
			"insertText": 
			{
				"objectId": titleId,
				"text": ("Team "+str(team_number)+": "+team_name),
			}
	    },
	    # FORMAT TITLE TEXT
	    {
	        'updateTextStyle': 
	        {
	            'objectId': titleId,
	            'textRange': 
	            {
	                'type': 'ALL',
	            },
	            'style': 
	            {
	                'fontFamily': 'Lato',
	                'bold': True,
	                'fontSize': 
	                {
	                    'magnitude': 36,
	                    'unit': 'PT'
	            	}
	            },
	            'fields': 'fontFamily,fontSize'
	        }
	    },
		# CREATE TEXT BOX FOR BODY TEXT
		{
	        'createShape': 
	        {
	            'objectId': bodyId,
	            'shapeType': 'TEXT_BOX',
	            'elementProperties': 
	            {
	                'pageObjectId': pageId,
	                'size': 
	                {
	                    'height': {'magnitude': 125, 'unit': 'PT'},
	                    'width': {'magnitude': 350, 'unit': 'PT'}
	                },
	                'transform': 
	                {
	                    'scaleX': 1,
	                    'scaleY': 1,
	                    'translateX': 50,
	                    'translateY': 250,
	                    'unit': 'PT'
	                }
	            }
	        }
    	},
    	# INSERT SCOUTING TEXT
    	{
    		'insertText': 
    		{
            	'objectId': bodyId,
            	'insertionIndex': 0,
            	'text': bodyText
        	}
        },
        # FORMAT SCOUTING TEXT
    	{
	        'updateTextStyle': 
	        {
	            'objectId': bodyId,
	            'textRange': 
	            {
	                'type': 'ALL',
	            },
	            'style': 
	            {
	            	'backgroundColor':
	            	{
	            		'opaqueColor':
	            		{
	            			'rgbColor':
	            			{
	            				'red': scouting_color("red",bodyText),
	            				'green': scouting_color("green",bodyText),
	            				'blue': scouting_color("blue",bodyText)
	            			}
	            		}
	            	},
	                'fontFamily': 'Lato',
	                'fontSize': 
	                {
	                    'magnitude': 18,
	                    'unit': 'PT'
	            	}
	            },
	            'fields': 'backgroundColor,fontFamily,fontSize'
	        }
	    }
    ))
	if (imageUrl):
		reqs.append(
	    	{
				"createImage": {
					"url": imageUrl,
					"elementProperties": 
					{
						"pageObjectId": pageId,
						"size": 
						{
							"width": {"magnitude": 400, "unit": "PT"},
							"height": {"magnitude": 300, "unit": "PT"}
						},
						"transform": 
						{
							"scaleX": 1,
							"scaleY": 1,
							"translateX": 400,
							"translateY": 100,
							"unit": "PT"
						}
					}
				}
			}
	    )
	for elem in team_data:
		if elem[0]==team:
			priorText = elem[4]+"\nRanked "+elem[1]+"\nW-L-T: "+elem[3]+"\nRanking Score: "+elem[2]
			reqs.append(
				# CREATE TEXT BOX FOR PRIOR COMPETITION
				{
			        'createShape': 
			        {
			            'objectId': priorId,
			            'shapeType': 'TEXT_BOX',
			            'elementProperties': 
			            {
			                'pageObjectId': pageId,
			                'size': 
			                {
			                    'height': {'magnitude': 100, 'unit': 'PT'},
			                    'width': {'magnitude': 250, 'unit': 'PT'}
			                },
			                'transform': 
			                {
			                    'scaleX': 1,
			                    'scaleY': 1,
			                    'translateX': 50,
			                    'translateY': 100,
			                    'unit': 'PT'
			                }
			            }
			        }
		    	}
		    	)
			reqs.append(
		    	# INSERT PRIOR COMPETITION TEXT
		    	{
		    		'insertText': 
		    		{
		            	'objectId': priorId,
		            	'insertionIndex': 0,
		            	'text': priorText
		        	}
		        }
		        )
			reqs.append(
		        # FORMAT PRIOR COMPETITION TEXT
		    	{
			        'updateTextStyle': 
			        {
			            'objectId': priorId,
			            'textRange': 
			            {
			                'type': 'ALL',
			            },
			            'style': 
			            {
			            	'backgroundColor':
			            	{
			            		'opaqueColor':
			            		{
			            			'rgbColor':
			            			{
			            				'red': prior_color("red",float(elem[2])),
			            				'green': prior_color("green",float(elem[2])),
			            				'blue': prior_color("blue",float(elem[2]))
			            			}
			            		}
			            	},
			                'fontFamily': 'Lato',
			                'fontSize': 
			                {
			                    'magnitude': 18,
			                    'unit': 'PT'
			            	}
			            },
			            'fields': 'backgroundColor,fontFamily,fontSize'
			        }
			    }
	    		)
	for elem in final_list:
		if elem[0]==team:
			currentText = elem[4]+"\nRanked "+elem[1]+"\nW-L-T: "+elem[3]+"\nRanking Score: "+elem[2]
			reqs.append(
				# CREATE TEXT BOX FOR CURRENT COMPETITION
				{
			        'createShape': 
			        {
			            'objectId': currentId,
			            'shapeType': 'TEXT_BOX',
			            'elementProperties': 
			            {
			                'pageObjectId': pageId,
			                'size': 
			                {
			                    'height': {'magnitude': 400, 'unit': 'PT'},
			                    'width': {'magnitude': 250, 'unit': 'PT'}
			                },
			                'transform': 
			                {
			                    'scaleX': 1,
			                    'scaleY': 1,
			                    'translateX': 250,
			                    'translateY': 100,
			                    'unit': 'PT'
			                }
			            }
			        }
		    	}
		    	)
			reqs.append(
		    	# INSERT CURRENT COMPETITION TEXT
		    	{
		    		'insertText': 
		    		{
		            	'objectId': currentId,
		            	'insertionIndex': 0,
		            	'text': currentText
		        	}
		        }
		        )
			reqs.append(
		        # FORMAT CURRENT COMPETITION TEXT
		    	{
			        'updateTextStyle': 
			        {
			            'objectId': currentId,
			            'textRange': 
			            {
			                'type': 'ALL',
			            },
			            'style': 
			            {
			            	'backgroundColor':
			            	{
			            		'opaqueColor':
			            		{
			            			'rgbColor':
			            			{
			            				'red': prior_color("red",float(elem[2])),
			            				'green': prior_color("green",float(elem[2])),
			            				'blue': prior_color("blue",float(elem[2]))
			            			}
			            		}
			            	},
			                'fontFamily': 'Lato',
			                'fontSize': 
			                {
			                    'magnitude': 18,
			                    'unit': 'PT'
			            	}
			            },
			            'fields': 'backgroundColor,fontFamily,fontSize'
			        }
			    }
	    		)		

reqs.append({"insertText": {"objectId": titleID, "text": "FRC 2018-2019 Scouting Data"}})
reqs.append({"insertText": {"objectId": subtitleID, "text": "via the Google Sheets and Slides API"}})
rsp = SLIDES.presentations().batchUpdate(body={'requests': reqs},
	presentationId=deckID).execute().get("replies")
print("DONE")
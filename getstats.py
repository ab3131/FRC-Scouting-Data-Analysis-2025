final_list = []

def parseTableForAlliances (table, event, amount):
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
			print(items)
			for elem in final_list:
				if elem[0]==items[0]:
					final_list.remove(elem)
			final_list.append(items)
			#row now contains data for each team in a list

def prepForFormatting (heading, teams, amount):
	for num in range(0,amount):
		team = teams[num][1:3]+(teams[num][8])
		f.write(title + "," + team.replace(" ", ",") + "\n")

f = open('output.txt','w')
f.truncate()
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
head_page = "https://www.thebluealliance.com/event/2023"
week1_codes = ["qcmo","scmb","caoc","migib","miket","misou","nhgrs","cadm","gagai","onosh","pahat","vagle","vahay","txelp","txaus","wamou","tuis","isde1","tuis2","isde2","nytr","ohmv","arli","ilch","mndu","mndu2","mxmo","okok","bcvi","cafr","casd","gadal","mibel","mike2","milak","mimil","misjo","txama","orwil","ctwat","inmis","mabri","mdbet","ncwak","njfla","onto3","txsan","pawch","waamv","ausc","isde3","isde4","flor","nyro","nyut","alhu","ksla","mosl","ndgf","mxcm","azfl","gaalb","micen","midet","migul","mimus","onto1","mikng","txcha","txpla","orore","wayak","caln","casf","ausp","marea","mdowi","ncgui","nhsnh","njbri","onbar","paphi","vapor","paca","iacf","ilpe","lake","mokc","code","mxto","cada","cala","gacol","mialp","mijac","milin","mimid","miwmi","onwat","txgre","waspo","nysu","camb","inwla","mabos","mawne","mdoxo","ncash","njtab","onnyo","rismi","txdel","wasno","nyli"]
ranks = [[],[],[],[],[],[],[],[]]
count = 1
error_events = []
for event_code in week1_codes:
	try:
		f.seek(0)
		f.truncate()
		f.seek(0) # I believe this seek is redundant
		print("Finding Event: "+event_code)
		quote_page = Request(head_page + event_code + "#rankings", headers={'User-Agent': 'Mozilla/5.0'})
		page = urlopen(quote_page)
		soup = BeautifulSoup(page, "html.parser")
		title = soup.find("h1", attrs={"itemprop": "summary"})
		title = title.text.strip()
		title = title[:-5]
		table = soup.find("table", attrs={"id": "rankingsTable"})
		if (table==None):
			print("Skipped Event " + event_code + ": No Data Found")
			error_events.append(event_code)
			count +=1
			continue
		teams = table.find_all('tr')
		teams = len(teams)
		teams -= 1
		print("Found "+str(teams)+" teams")
		print("Copying information from Event "+str(count)+"/"+str(len(week1_codes))+": "+title)
		parseTableForAlliances(table, title, teams)
		count += 1
	except:
		print("Skipping Event "+event_code+" due to error.")
		error_events.append(event_code)
f.write(str(final_list))
f.close()
print("Here are the events skipped:")
print(error_events)
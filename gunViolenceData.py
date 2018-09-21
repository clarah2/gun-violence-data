import csv
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict

urlList = []

# function to get list of incident links from each mass shooting page (http://www.gunviolencearchive.org/reports/mass-shooting)

def get_urls(url):
	response = requests.get(url, timeout = 10)
	soup = BeautifulSoup(response.content, 'html.parser')
	table = soup.find('table', class_="responsive sticky-enabled")
	rows = table.select('tbody > tr')
	
	for row in rows:
		urlList.append(row.find('a').attrs['href'])
	
	for x in range(0, len(urlList)):
		urlList[x] = 'http://www.gunviolencearchive.org' + urlList[x]
	
# function to get the information from each incident page (ex. http://www.gunviolencearchive.org/incident/604762) 
# creates 3 csv files: basics, participants, and guns, preceded by unique ID number. One of each for each incident
# also prints the notes and incident characteristics

def get_info(url):
	if "http://www.gunviolencearchive.org/incident/" in url:
		iD = url.split("http://www.gunviolencearchive.org/incident/")
		incidentString = iD[1]
		incidentNumber = int(incidentString)
	else:
		print('URL not valid')
		return
	response = requests.get(url, timeout = 10)
	soup = BeautifulSoup(response.content, 'html.parser')
	headers = soup.find_all('h2')
	basicInfo = {'Incident' : incidentNumber}
	for h in headers:

		if "Location" in h.text:

			info = h.findNextSibling('h3')
			location = []
			basicInfo['Date'] = info.text
			while info != None:
				info = info.findNextSibling('span')
				if info == None:
					break
				location.append(info.text)
			locationLength = len(location)

			# some incidents just provide street address (length is 3), others also have a place name which means there is one more 'span' element (length is 4)
			if locationLength == 4:
				basicInfo['Geolocation'] = location[3].split("Geolocation: ")[1]
				basicInfo['City, State'] = location[2]
				basicInfo['Address'] = location[1]
				basicInfo['Place Name'] = location[0]
			elif locationLength == 3:
				basicInfo['Geolocation'] = location[2].split("Geolocation: ")[1]
				basicInfo['City, State'] = location[1]
				basicInfo['Address'] = location[0]

			continue

		elif "Participant" in h.text:
			
			csvName = incidentString + 'participants.csv'
			participantCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Name', None), ('Age', None), ('Age Group', None), ('Gender', None), ('Status', None)])
			partDiv = h.findNextSibling('div')
			uls = partDiv.findChildren('ul')
			participantList = []

			# creates a dictionary for each participant with all of their info and adds it to participantList
			for ul in uls:
				participant = {'Incident' : incidentNumber}
				for li in ul:
					data = str(li)		#change each li entry to string
					fact = data[4:-5]	#remove <li> and </li> from beginning and end

					#for each fact, remove field name and add to participant dictionary
					if "Type:" in fact:
						participant['Type'] = fact.split("Type: ")[1]
					elif "Name:" in fact:
						participant['Name'] = fact.split("Name: ")[1]
					elif "Age:" in fact:
						participant['Age'] = fact.split("Age: ")[1]
					elif "Age Group:" in fact:
						participant['Age Group'] = fact.split("Age Group: ")[1]
					elif "Gender:" in fact:
						participant['Gender'] = fact.split("Gender: ")[1]
					elif "Status:" in fact:
						participant['Status'] = fact.split("Status: ")[1]
				participantList.append(participant)

			#write participant headers and data to csv
			with open(csvName, 'w') as csvFile:
				participantHeaders = csv.DictWriter(csvFile, fieldnames = participantCharacteristics)
				participantHeaders.writeheader()
				for participant in participantList:
					participantHeaders.writerow(participant)

			continue

		elif "Incident Characteristics" in h.text:

			info = h.findNextSibling('ul')
			li = info.findChildren('li')
			incidentCharacteristics = []
			for child in li:
				incidentCharacteristics.append(child.text)
			#print(incidentCharacteristics)

			continue

		elif "Notes" in h.text:

			info = h.findNextSibling('p').text
			#print(info)

			continue

		elif "Guns Involved" in h.text:

			csvName = incidentString + 'guns.csv'
			gunCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Stolen', None)])
			info = h.findNextSibling('ul')
			gunList = []

			for guns in h:
				while info != None:
					gunFacts = info.findChildren('li', recursive = False)
					gun = {'Incident' : incidentNumber}
					for child in gunFacts:
						if "Type:" in child.text:
							gun['Type'] = child.text.split("Type: ")[1]
						elif "Stolen:" in child.text:
							gun['Stolen'] = child.text.split("Stolen: ")[1]
					gunList.append(gun)
					info = info.findNextSibling('ul')

			with open(csvName, 'w') as csvFile:
				gunHeaders = csv.DictWriter(csvFile, fieldnames = gunCharacteristics)
				gunHeaders.writeheader()
				for myGun in gunList:
					gunHeaders.writerow(myGun)

			continue

		elif "District" in h.text:
			districtText = h.parent.text
			districtText = districtText.splitlines()
			basicInfo['Congressional District'] = districtText[2].split("Congressional District: ")[1]
			basicInfo['State Senate District'] = districtText[3].split("State Senate District: ")[1]
			basicInfo['State House District'] = districtText[4].split("State House District: ")[1]
			
			continue

	basics = OrderedDict([('Incident', None), ('Date', None), ('Place Name', None), ('Address', None), ('City, State', None), ('Geolocation', None), ('Congressional District', None), ('State Senate District', None), ('State House District', None)])
	
	csvName = incidentString + 'basics.csv'
	with open(csvName, 'w') as csvFile:
		basicsHeaders = csv.DictWriter(csvFile, fieldnames = basics)
		basicsHeaders.writeheader()
		basicsHeaders.writerow(basicInfo)

if __name__=="__main__":
	
	#url = "http://www.gunviolencearchive.org/incident/1206828"
	#get_info(url)

	# for all links from one page of mass shootings
	get_urls("http://www.gunviolencearchive.org/reports/mass-shooting")
	for URL in urlList:
		get_info(URL)





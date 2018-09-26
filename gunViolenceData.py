import csv
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict


# function to get list of incident links from each mass shooting page (http://www.gunviolencearchive.org/reports/mass-shooting)

def get_urls(url):
	response = requests.get(url, timeout = 10)
	soup = BeautifulSoup(response.content, 'html.parser')
	table = soup.find('table', class_="responsive sticky-enabled")
	rows = table.select('tbody > tr')

	urlList = ['http://www.gunviolencearchive.org' + row.find('a').attrs['href'] for row in rows]

	return urlList
	
# function to get the information from each incident page (ex. http://www.gunviolencearchive.org/incident/604762) 
# creates 3 csv files: basics, participants, and guns, preceded by unique ID number. One of each for each incident
# also prints the notes and incident characteristics

def scrape_urls(url):
	if url.startswith("http://www.gunviolencearchive.org/incident/"):
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

			locationInfo = h.findNextSibling('h3')
			location = []
			basicInfo['Date'] = locationInfo.text
			while locationInfo is not None:
				locationInfo = locationInfo.findNextSibling('span')
				if locationInfo is None:
					break
				location.append(locationInfo.text)
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
			else: 	#if locationLength < 3 or > 4
				print('Unexpected number of location items for incident ' + incidentString)
				continue

		elif "Participant" in h.text:
			
			csvName = incidentString + 'participants.csv'
			participantCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Relationship', None), ('Name', None), ('Age', None), ('Age Group', None), ('Gender', None), ('Status', None)])
			partDiv = h.findNextSibling('div')
			uls = partDiv.findChildren('ul')
			participantList = []

			# creates a dictionary for each participant with all of their info and adds it to participantList
			for ul in uls:
				participant = {'Incident' : incidentNumber}
				for li in ul:
					data = str(li)		#change each li entry to string
					fact = data[4:-5]	#remove <li> and </li> from beginning and end
					
					#for each fact, split at colon and create key value pair to add to participant dictionary
					if len(fact) > 0: #to account for li of empty string

						splitFact = fact.split(": ")
						key, value = splitFact[0], splitFact[1]
						participant[key] = value

				participantList.append(participant)

			#write participant headers and data to csv
			with open(csvName, 'w') as csvFile:
				participantHeaders = csv.DictWriter(csvFile, fieldnames = participantCharacteristics)
				participantHeaders.writeheader()
				for participant in participantList:
					participantHeaders.writerow(participant)

		elif "Incident Characteristics" in h.text:

			ICinfo = h.findNextSibling('ul')
			li = ICinfo.findChildren('li')
			incidentCharacteristics = [child.text for child in li]
			#print(incidentCharacteristics)

			continue

		elif "Notes" in h.text:

			#print(h.findNextSibling('p').text)
			continue

		elif "Guns Involved" in h.text:

			csvName = incidentString + 'guns.csv'
			gunCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Stolen', None)])
			gunInfo = h.findNextSibling('ul')
			gunList = []

			for guns in h:
				while gunInfo is not None:
					gunFacts = gunInfo.findChildren('li', recursive = False)
					gun = {'Incident' : incidentNumber}
					for child in gunFacts:
						if "Type:" in child.text:
							gun['Type'] = child.text.split("Type: ")[1]
						elif "Stolen:" in child.text:
							gun['Stolen'] = child.text.split("Stolen: ")[1]
					gunList.append(gun)
					gunInfo = gunInfo.findNextSibling('ul')

			with open(csvName, 'w') as csvFile:
				gunHeaders = csv.DictWriter(csvFile, fieldnames = gunCharacteristics)
				gunHeaders.writeheader()
				for myGun in gunList:
					gunHeaders.writerow(myGun)

		elif "District" in h.text:
			districtText = h.parent.text
			districtText = districtText.splitlines()
			
			for item in districtText:
				districtFact = item.split(": ")
				if len(districtFact) == 2:
					key, value = districtFact[0], districtFact[1]
					basicInfo[key] = value
			

	basics = OrderedDict([('Incident', None), ('Date', None), ('Place Name', None), ('Address', None), ('City, State', None), ('Geolocation', None), ('Congressional District', None), ('State Senate District', None), ('State House District', None)])
	
	csvName = incidentString + 'basics.csv'
	with open(csvName, 'w') as csvFile:
		basicsHeaders = csv.DictWriter(csvFile, fieldnames = basics)
		basicsHeaders.writeheader()
		basicsHeaders.writerow(basicInfo)

if __name__=="__main__":
	
	# sample URL for scrape_urls function
	#url = "http://www.gunviolencearchive.org/incident/604762"
	#scrape_urls(url)

	# for all links from one page of mass shootings
	links = get_urls("http://www.gunviolencearchive.org/reports/mass-shooting")
	for URL in links:
		scrape_urls(URL)





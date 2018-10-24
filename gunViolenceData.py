import csv
import requests
import pandas as pd
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

# function to add list of dictionaries (data) to certain csv (category) with headers (fields)

def write_to_csv(category, data, fields):
	df = pd.DataFrame.from_dict(data)
	with open(category + '.csv', 'a') as f:
		f.write('\n')
		df.to_csv(f, header=False, index=False, columns = fields)


#function creates five csv files: Basics, Participants, IncidentCharacteristics, Notes, Guns to fill with data

def create_csv():
	basics = OrderedDict([('Incident', None), ('Date', None), ('Place Name', None), ('Address', None), ('City', None), ('State', None), ('Latitude', None), ('Longitude', None), ('Congressional District', None), ('State Senate District', None), ('State House District', None)])
	participantCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Relationship', None), ('Name', None), ('Age', None), ('Age Group', None), ('Gender', None), ('Status', None)])
	iC = OrderedDict([('Incident', None), ('Incident Characteristic', None)])
	notes = OrderedDict([('Incident', None), ('Notes', None)])
	gunCharacteristics = OrderedDict([('Incident', None), ('Gun Type', None), ('Stolen', None)])
	
	with open('Basics.csv', 'w') as csvFile:
		basicsHeaders = csv.DictWriter(csvFile, fieldnames = basics)
		basicsHeaders.writeheader()

	with open('Participants.csv', 'w') as csvFile:
		participantHeaders = csv.DictWriter(csvFile, fieldnames = participantCharacteristics)
		participantHeaders.writeheader()

	with open('IncidentCharacteristics.csv', 'w') as csvFile:
		iCHeaders = csv.DictWriter(csvFile, fieldnames = iC)
		iCHeaders.writeheader()

	with open('Notes.csv', 'w') as csvFile:
		notesHeaders = csv.DictWriter(csvFile, fieldnames = notes)
		notesHeaders.writeheader()

	with open('Guns.csv', 'w') as csvFile:
		gunHeaders = csv.DictWriter(csvFile, fieldnames = gunCharacteristics)
		gunHeaders.writeheader()



	
# function to get the information from each incident page (ex. http://www.gunviolencearchive.org/incident/604762) 
# creates 3 csv files: basics, participants, and guns, preceded by unique ID number. One of each for each incident
# also prints the notes and incident characteristics

def scrape_urls(url):
	
	# checking that user provided valid link
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

	basicInfo = [{'Incident' : incidentNumber, 'Date': None, 'Place Name': None, 'Address': None, 'City': None, 'State': None, 'Latitude': None, 'Longitude': None, 'Congressional District': None, 'State Senate District': None, 'State House District': None}]
	basicsHeaders = [x for x in basicInfo[0].keys()] #create list of headers

	#going through all headers in link to find information
	for h in headers:

		if "Location" in h.text:

			locationInfo = h.findNextSibling('h3')
			location = []
			basicInfo[0]['Date'] = locationInfo.text
			while locationInfo is not None:
				locationInfo = locationInfo.findNextSibling('span')
				if locationInfo is None:
					break
				location.append(locationInfo.text)
			locationLength = len(location)

			# some incidents just provide street address (length is 3), others also have a place name which means there is one more 'span' element (length is 4)
			if locationLength == 4:
				geolocation = location[3].split("Geolocation: ")[1]
				basicInfo[0]['Latitude'] = geolocation.split(",")[0]
				basicInfo[0]['Longitude'] = geolocation.split(",")[1]
				basicInfo[0]['City'] = location[2].split(", ")[0]
				basicInfo[0]['State'] = location[2].split(", ")[1]
				basicInfo[0]['Address'] = location[1]
				basicInfo[0]['Place Name'] = location[0]
			elif locationLength == 3:
				geolocation = location[2].split("Geolocation: ")[1]
				basicInfo[0]['Latitude'] = geolocation.split(",")[0]
				basicInfo[0]['Longitude'] = geolocation.split(",")[1]
				basicInfo[0]['City'] = location[1].split(", ")[0]
				basicInfo[0]['State'] = location[1].split(", ")[1]
				basicInfo[0]['Address'] = location[0]
			else: 	#if locationLength < 3 or > 4
				print('Unexpected number of location items for incident ' + incidentString)
				continue

		elif "Participant" in h.text:
			
			partDiv = h.findNextSibling('div')
			uls = partDiv.findChildren('ul')
			participantList = []

			# creates a dictionary for each participant with all of their info and adds it to participantList
			for ul in uls:
				participant = {'Incident' : incidentNumber, 'Type': None, 'Relationship': None, 'Name': None, 'Age': None, 'Age Group': None, 'Gender': None, 'Status': None}
				for li in ul:
					data = str(li)		#change each li entry to string
					fact = data[4:-5]	#remove <li> and </li> from beginning and end
					
					#for each fact, split at colon and modify key value pair in participant dictionary
					if len(fact) > 0: #to account for li of empty string

						splitFact = fact.split(": ")
						key, value = splitFact[0], splitFact[1]
						participant[key] = value

				participantList.append(participant)

			participantsHeaders = [x for x in participantList[0].keys()] #create list of headers
			write_to_csv('Participants', participantList, participantsHeaders) #add all dictionaries in participantList to Participants.csv
			
		elif "Incident Characteristics" in h.text:

			ICinfo = h.findNextSibling('ul')
			li = ICinfo.findChildren('li')
			incidentCharacteristics = [{'Incident': incidentNumber, 'Incident Characteristic': child.text} for child in li]
			
			iCHeaders = [x for x in incidentCharacteristics[0].keys()] #create list of headers
			write_to_csv('IncidentCharacteristics', incidentCharacteristics, iCHeaders) #add incident characteristics to IncidentCharacteristics.csv

		elif "Notes" in h.text:

			txt = h.findNextSibling('p').text
			notes = [{'Incident': incidentNumber, 'Notes': txt}]

			notesHeaders = [x for x in notes[0].keys()] #create list of headers
			write_to_csv('Notes', notes, notesHeaders) #add notes to Notes.csv

		elif "Guns Involved" in h.text:

			gunInfo = h.findNextSibling('ul')
			gunList = []

			for guns in h:
				while gunInfo is not None:
					gunFacts = gunInfo.findChildren('li', recursive = False)
					gun = {'Incident' : incidentNumber, 'Gun Type': None, 'Stolen': None}
					for child in gunFacts:
						if "Type:" in child.text:
							gun['Gun Type'] = child.text.split("Type: ")[1]
						elif "Stolen:" in child.text:
							gun['Stolen'] = child.text.split("Stolen: ")[1]
					gunList.append(gun)
					gunInfo = gunInfo.findNextSibling('ul')
			
			gunsHeaders = [x for x in gunList[0].keys()] #create list of headers
			write_to_csv('Guns', gunList, gunsHeaders) #add guns to Guns.csv


		elif "District" in h.text:
			districtText = h.parent.text
			districtText = districtText.splitlines()
			
			for item in districtText:
				districtFact = item.split(": ")
				if len(districtFact) == 2:
					key, value = districtFact[0], districtFact[1]
					basicInfo[0][key] = value

	#add basic info to Basics.csv
	write_to_csv('Basics', basicInfo, basicsHeaders)
	

if __name__=="__main__":
	
	# to create csvs to start collecting data
	#create_csv()

	# for just one url, use scrape_urls function
	url = "http://www.gunviolencearchive.org/incident/604762"
	scrape_urls(url)

	# for many urls, use get_urls to get a list of urls first
	#links = get_urls("https://www.gunviolencearchive.org/query/83c968ab-971c-4bb0-8bac-1d08f396095f")
	#for URL in links:
	#	scrape_urls(URL)





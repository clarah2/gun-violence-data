import csv
import requests
import pandas as pd
from bs4 import BeautifulSoup
from collections import OrderedDict



'''function to get list of incident links from each mass shooting (or other report or query) page (http://www.gunviolencearchive.org/reports/mass-shooting)'''

def get_urls(url):
	response = requests.get(url, timeout = 10)
	soup = BeautifulSoup(response.content, 'html.parser')
	table = soup.find('table', class_="responsive sticky-enabled")
	rows = table.select('tbody > tr')

	urlList = ['http://www.gunviolencearchive.org' + row.find('a').attrs['href'] for row in rows]

	return urlList



'''get_all_urls function gets all incident links from a mass shooting page, as well as the incident links from all the following mass shooting pages. Works for "Reports" pages, as well as "Search Database" results. Call the function with url input for the first page of any of these results, and function will return longUrlList with all the incident links from the first page and all the subsequent pages. '''

#initiate empty list to fill with multiple links from multiple pages
longUrlList = []

def get_all_urls(url):
	#get all "View Incident" links from one page, as done in get_urls function
	response = requests.get(url, timeout = 10)
	soup = BeautifulSoup(response.content, 'html.parser')
	table = soup.find('table', class_="responsive sticky-enabled")
	rows = table.select('tbody > tr')
	
	#add the "View Incident" links to a list
	urlList = ['http://www.gunviolencearchive.org' + row.find('a').attrs['href'] for row in rows]
	#add links from urlList to the bigger list of links
	for link in urlList:
		longUrlList.append(link)
	
	#find out if there is another "next" page of incidents
	nextPageLink = soup.find_all('li', {'class':"pager-next"})

	#if a "next" page exists, call function on the link to that "next" page
	if nextPageLink != []:
		addToUrl = nextPageLink[0].find('a').attrs['href']
		newUrl = 'https://www.gunviolencearchive.org' + addToUrl
		get_all_urls(newUrl)
	#when there are no more pages of links, return the longUrlList, for use with scrape_urls function
	else:
		return longUrlList





	

'''function to add list of dictionaries (data) to certain csv (category) with headers (fields)'''

def write_to_csv(category, data, fields):
	df = pd.DataFrame.from_dict(data)
	with open(category + '.csv', 'a') as f:
		df.to_csv(f, header=False, index=False, columns = fields)


'''function creates 4 csv files: Basics, Participants, IncidentCharacteristics, Guns to fill with data'''

def create_csv():
	basics = OrderedDict([('Incident', None), ('Date', None), ('Place Name', None), ('Address', None), ('City', None), ('State', None), ('Latitude', None), ('Longitude', None), ('Congressional District', None), ('State Senate District', None), ('State House District', None), ('Participant Count', None), ('Victim Count', None), ('Subject Count', None), ('Gun Count', None), ('Notes', None)])
	participantCharacteristics = OrderedDict([('Incident', None), ('Type', None), ('Relationship', None), ('Name', None), ('Age', None), ('Age Group', None), ('Gender', None), ('Status', None)])
	iC = OrderedDict([('Incident', None), ('Incident Characteristic', None)])
	gunCharacteristics = OrderedDict([('Incident', None), ('Gun Type', None), ('Stolen', None)])
	
	with open('Basics.csv', 'w') as csvFile:
		basicsHeaders = csv.DictWriter(csvFile, fieldnames = basics)
		basicsHeaders.writeheader()
		csvFile.write('\n')

	with open('Participants.csv', 'w') as csvFile:
		participantHeaders = csv.DictWriter(csvFile, fieldnames = participantCharacteristics)
		participantHeaders.writeheader()
		csvFile.write('\n')

	with open('IncidentCharacteristics.csv', 'w') as csvFile:
		iCHeaders = csv.DictWriter(csvFile, fieldnames = iC)
		iCHeaders.writeheader()
		csvFile.write('\n')

	with open('Guns.csv', 'w') as csvFile:
		gunHeaders = csv.DictWriter(csvFile, fieldnames = gunCharacteristics)
		gunHeaders.writeheader()
		csvFile.write('\n')



	
'''function to get the information from each incident page (ex. http://www.gunviolencearchive.org/incident/604762), puts all data into one of 4 csv files created by create_csv()'''

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

	basicInfo = [{'Incident' : incidentNumber, 'Date': None, 'Place Name': None, 'Address': None, 'City': None, 'State': None, 'Latitude': None, 'Longitude': None, 'Congressional District': None, 'State Senate District': None, 'State House District': None, 'Participant Count': None, 'Victim Count': None, 'Subject Count': None, 'Gun Count': None, 'Notes': None}]
	basicsHeaders = [x for x in basicInfo[0]] #create list of headers

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
			victimCount = 0
			subjectCount = 0
			participantCount = 0

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
				
				#counter variables for numbers of victims and subjects
				if participant['Type'] == "Victim":
					victimCount += 1
				elif participant['Type'] == "Subject-Suspect":
					subjectCount += 1
				
				participantList.append(participant)

			participantCount = victimCount + subjectCount #counter variable for total number of participants
			basicInfo[0]['Participant Count'] = participantCount
			basicInfo[0]['Victim Count'] = victimCount
			basicInfo[0]['Subject Count'] = subjectCount

			participantsHeaders = [x for x in participantList[0]] #create list of headers
			write_to_csv('Participants', participantList, participantsHeaders) #add all dictionaries in participantList to Participants.csv
			
		elif "Incident Characteristics" in h.text:

			ICinfo = h.findNextSibling('ul')
			li = ICinfo.findChildren('li')
			incidentCharacteristics = [{'Incident': incidentNumber, 'Incident Characteristic': child.text} for child in li]
			
			iCHeaders = [x for x in incidentCharacteristics[0]] #create list of headers
			write_to_csv('IncidentCharacteristics', incidentCharacteristics, iCHeaders) #add incident characteristics to IncidentCharacteristics.csv

		elif "Notes" in h.text:

			txt = h.findNextSibling('p').text
			basicInfo[0]['Notes'] = txt

		elif "Guns Involved" in h.text:

			gunInfo = h.findNextSibling('ul')
			gunList = []
			gunCount = 0

			for guns in h:
				while gunInfo is not None:
					gunFacts = gunInfo.findChildren('li', recursive = False)
					gun = {'Incident' : incidentNumber, 'Gun Type': None, 'Stolen': None}
					gunCount += 1
					for child in gunFacts:
						if "Type:" in child.text:
							gun['Gun Type'] = child.text.split("Type: ")[1]
						elif "Stolen:" in child.text:
							gun['Stolen'] = child.text.split("Stolen: ")[1]
					gunList.append(gun)
					gunInfo = gunInfo.findNextSibling('ul')

			basicInfo[0]['Gun Count'] = gunCount
			
			gunsHeaders = [x for x in gunList[0]] #create list of headers
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
	create_csv()

	# for just one url, use scrape_urls function
	url = "http://www.gunviolencearchive.org/incident/604762"  #using incident 604762 as an example
	scrape_urls(url)

	# for many urls, use get_urls to get a list of urls first
	#links = get_urls("https://www.gunviolencearchive.org/query/83c968ab-971c-4bb0-8bac-1d08f396095f")
	#for URL in links:
	#	scrape_urls(URL)

	#gets all urls from results of the query, can then loop over list to scrape data as demonstrated in example above
	#get_all_urls('https://www.gunviolencearchive.org/query/a8aef44c-ca1e-43a5-a40c-ffe766853cde')
	




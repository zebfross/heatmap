import urllib2
import urllib
from bs4 import BeautifulSoup
import time
import csv
import re
import json
from datetime import datetime
import query_db as db
import sys
sys.path.append('/home6/zebfross/secret')
import googleapi

google_map_regex = re.compile("^http://maps.google.com/\?q=loc%3A\+(.+$)");
post_id_regex = re.compile("PostingID:\W*(\d+)");
price_regex = re.compile("\$(\d{1,3},?)*\d+\.?");
date_regex = re.compile("Date:\W*([0-9]{1,4}-[0-9]{1,2}-[0-9]{1,2},( *)[0-9]{1,2}:[0-9]{1,2}(AM|PM)\W*\w{3})");

key = googleapi.key
google_url_base = "http://maps.googleapis.com/maps/api/geocode/json?sensor=false&address="
states=['wyoming']

def getInfoForLocation(location):
	link = google_url_base + urllib.quote_plus(location)
	print link
	try:
		google_request = urllib2.urlopen(link)
		raw_resp = google_request.read();
	except:
		print "Error opening link: " + link
		return {}
	
	json_resp = json.loads(raw_resp)
	if json_resp["status"] != "OK":
		print "Google Response: " + json_resp["status"]
		return {}

	address = json_resp["results"][0]["formatted_address"]
	latitude = json_resp["results"][0]["geometry"]["location"]["lat"]
	longitude = json_resp["results"][0]["geometry"]["location"]["lng"]

	return {"address": address, "latitude": latitude, "longitude": longitude}

def findLocationInAd(ad_soup):
	for a in ad_soup.findAll("a"):
		# search for "google map" link in ad
		if a.string != "google map":
			continue;
		result = google_map_regex.match(a["href"])
		if not result or result.groups < 2:
			break;
		location = urllib.unquote_plus(result.group(1));
		return {"location": location}

	return {}

def findPostIdInAd(ad_soup):
	post_id_match = post_id_regex.search(ad_soup.get_text());
	if post_id_match and post_id_match.groups > 1:
		post_id = post_id_match.group(1)
		return {"post_id": post_id}
	return {}

def findPriceInAd(ad_soup):
	price_match = price_regex.search(ad_soup.get_text());
	if price_match:
		price = price_match.group(0)
		return {"price": price}
	return {}

def findPostDateInAd(ad_soup):
	date_match = date_regex.search(ad_soup.get_text());
	if date_match:
		posted_at = date_match.group(1)
		return {"posted_at": posted_at}
	return {}

def getInfoForAd(ad_link):
	try:
		ad_request = urllib2.urlopen(ad_link)
		ad_html = ad_request.read();
	except:
		print "Error opening link: " + ad_link
		return []
	ad_soup = BeautifulSoup(ad_html);

	link_info = {"url": ad_link}
	post_id_info = findPostIdInAd(ad_soup)
	price_info = findPriceInAd(ad_soup)
	date_info = findPostDateInAd(ad_soup)
	location = findLocationInAd(ad_soup)
	if not location: return {}
	address_info = getInfoForLocation(location["location"])
	if not address_info:
		return {}
	return dict(
	link_info.items() +
	post_id_info.items() + 
	price_info.items() + 
	date_info.items() +
	address_info.items())

def getUrlForStateAndPaging(state, paging=0):
	url = 'http://%s.craigslist.org/rea/' %state
	if paging > 0:
		url += 'index%d.html' %(paging * 100)
	return url

# removes commas and dollar signs
def formatPrice(raw_price):
	return re.sub(r'(\$|,)', "", raw_price);

def formatDate(raw_date):
	post_date = datetime.strptime(raw_date, "%Y-%m-%d, %I:%M%p %Z")
	return post_date.strftime("%Y-%m-%d %H:%M:%S")

def formatCurrentDate():
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def getPropertiesForState(state, target_num=100):
	num_passes = 0
	results = []
	while len(results) < target_num:
		url = getUrlForStateAndPaging(state, num_passes)
		request = urllib2.urlopen(url)
		html = request.read()
		soup=BeautifulSoup(html)

		# ad links are stored in <p>s
		for p in soup.findAll("p"):
			links = p.findAll("a")
			if len(links) == 0:
				continue
			link = links[0] # ad links are always the first link in the <p>
			link_href = link["href"];
			info = getInfoForAd(link_href)

			if not info: continue

			results.append(info)
			formatProperties([info])
			fillDatabaseWithProperties([info])
			if len(results) > target_num: break
	
		num_passes += 1 # finished processing page
	return results

def dbHasId(id):
	try:
		query = "select id from property where id='" + id + "'"
		rows = db.executeQuery(query)
		return len(rows) > 0
	except:
		print "error selecting item with id: " + id
		return 0

def updateProperty(prop):
	query = """
		update property set url = '%s', crawled_at = '%s'
		where id = '%s'
	""" % (prop["url"], formatCurrentDate(), prop["id"])

	db.executeUpdate(query)
	
def insertNewProperty(prop):
	query = """
		insert into property 
		(id, address, longitude, latitude, price, url, posted_at, crawled_at) values
			('%s', '%s', %s, %s, %s, '%s', '%s', '%s')
	""" % (prop["id"], 
	prop["address"], 
	prop["longitude"], 
	prop["latitude"], 
	prop["price"], 
	prop["url"],
	prop["posted_at"],
	formatCurrentDate())

	db.executeUpdate(query)

def fillDatabaseWithProperties(properties):
	db.openDbConnection()
	for property in properties:
		if "id" not in property:
			continue
		if dbHasId(property["id"]):
			updateProperty(property)
		else:
			insertNewProperty(property)
	db.closeDbConnection()

def formatProperties(properties):
	for property in properties:
		if "price" in property:
			property["price"] = formatPrice(property["price"])
		else:
			properties.remove(property)
			continue
		if "post_id" in property:
			property["id"] = "C" + property["post_id"]
		if "posted_at" in property:
			property["posted_at"] = formatDate(property["posted_at"])

def scrapeCL(state, target_num):
	properties = getPropertiesForState(state, target_num)
	#formatProperties(properties)
	#fillDatabaseWithProperties(properties)

scrapeCL("wyoming", 1)


# First_Spider
1. List of website:
http://search.211childcare.org/
https://idahostars.org/Providers/Child-Care-Licensing,%20select
http://families.decal.ga.gov/ChildCare/Search
https://secure.dss.ca.gov/CareFacilitySearch/?SearchReWrite=ChildCare
https://cares.myflfamilies.com/PublicSearch
http://www.dss.virginia.gov/facility/search/cc.cgi
https://www.findchildcarewa.org/PSS_Search?ft=Child%20Care%20Center;Family%20Child%20Care%20Home&p=DEL%20Licensed;Unlicensed%20Facility&PSL-0030=Open
http://www.coloradoshines.com/search
http://www.checkccmd.org/SearchResults.aspx?ft=&fn=&sn=&z=&c=&co=
https://childcarefinder.wisconsin.gov/Search/Search.aspx

2. Purpose:
- Scrape all Day Care Centers Infomations from 10 state of US (10 sites).

3. How:
- Create 10 Scrapy Spider in First_Spider/First_Spider/Spiders.
- Run: Type following in command promt: scrapy crawl Spider_Name -o Spider_Data.json
- Please change Spider_Name with one of 10 Spider name (define by attribute name inside each spider class).
- Please change Spider_Data to the file name you want to save the data to.

Notes: 
- Some spider require List Zip of that state to start scraping process. Please save List zip and an excel file with Zip header and followed by Zip Code.
- Name the List Zip with List_Zip.csv and save it in First_Spider/First_Spider.

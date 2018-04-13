import scrapy
import regex
import json
from bs4 import BeautifulSoup
import pandas

class QuotesSpider(scrapy.Spider):
    name = "GR_Spider"
    Main_Url=r"http://families.decal.ga.gov/api/provider/searchByAddress?providerNumber=&name=&zipCode={0}&qrOnly=&programType=&latitudeLongitude=|&radiusAroundAddress=&servicesProvided=&transportation=&otherChildCareType=&specialHours=&acceptingChildrenType=&campCare=&meals=&financialInfo=&minimumFullDayRate=&registrationFee=&activityFee=&daysOfOperation=&openTime=&closeTime=&preKSlots=&minAge=&maxAge=&languages=&environment=&activities="
    Detail_Url=r"http://families.decal.ga.gov/ChildCare/detail/"
    Filter_Field='ID'
    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        }
    }
    
    try:
        List_Zip_Url=r"C:\Users\Admin\Desktop\List Zip.csv"
        List_Zip=pandas.read_csv(List_Zip_Url)
    except:pass

    Normal_Title={'ID':'Id','BUSINESS_NAME':'location_name','FIRST_NAME':'Admin_FirstName','LAST_NAME':'Admin_LastName','TYPE':'ChildCareType',
                  'CITY':'ST_City','ADDRESS':'ST_Address','ZIP':'ST_Zip','STATE':'ST_State',
                  'PHONE':'Location_Phone','WEBSITE':'Location_Website','CAPACITY':'Capacity'}

    def start_requests(self):
        for index,city in self.List_Zip.iterrows():
            yield scrapy.Request(url=self.Main_Url.format(city['ZIP']),callback=self.parse,dont_filter=True)

    def parse(self, response):
        Soup=BeautifulSoup(response.text,'lxml')
        Result_List=json.loads(Soup.text)

        for record in Result_List:
            Temp_Dict = dict()
            for key,value in self.Normal_Title.items():
                Temp_Dict[key]=record[value]
            yield scrapy.Request(url=self.Detail_Url+str(Temp_Dict['ID']),meta={'Temp_Dict':Temp_Dict},dont_filter=True,callback=self.parse_detail)

    def parse_detail(self,response):
        Temp_Dict = response.meta.get('Temp_Dict')
        if response.css('#Content_Main_gvFacilityRates'):
            Soup=BeautifulSoup(response.css('#Content_Main_gvFacilityRates').extract_first(),'html.parser')

            Get_Rate=regex.compile(r"[-+]?\d*\.\d+",regex.IGNORECASE)
            Get_Lower_Rate = regex.compile(r"[-+]?\d*\.\d+(?=\-\$)", regex.IGNORECASE)
            Get_Upper_Rate = regex.compile(r"(?<=\-\$)[-+]?\d*\.\d+", regex.IGNORECASE)

            Rate_Header=[]

            Html_Colection=Soup.find_all("th")
            for htmlelem in Html_Colection:
                Rate_Header.append(htmlelem.text)

            Html_Colection=Soup.find_all("tr")
            for trelement in Html_Colection:
                    Td_Collection=trelement.find_all("td")
                    for se_pos in range(len(Td_Collection)):
                        if se_pos==0:
                            Posfix=Td_Collection[se_pos].text
                            continue
                        if Get_Lower_Rate.search(Td_Collection[se_pos].text):
                            Temp_Dict[Rate_Header[se_pos] + " " + Posfix] = str(Get_Lower_Rate.search(Td_Collection[se_pos].text).group())+"-"+str(Get_Upper_Rate.search(Td_Collection[se_pos].text).group())
                        elif Get_Rate.search(Td_Collection[se_pos].text):
                            Temp_Dict[Rate_Header[se_pos]+" "+Posfix]=str(Get_Rate.search(Td_Collection[se_pos].text).group())

        yield Temp_Dict



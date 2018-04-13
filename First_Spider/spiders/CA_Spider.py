import scrapy
import json
import pandas

class QuotesSpider(scrapy.Spider):
    name = "CA_Spider"

    Main_Url=r"https://secure.dss.ca.gov/ccld/TransparencyAPI/api/FacilitySearch?facType={0}&facility=&Street=&city=&zip={1}&county="
    Detail_Url=r"https://secure.dss.ca.gov/ccld/TransparencyAPI/api/FacilityDetail/{0}"

    Filter_Field='ID'

    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        },
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200
        },

    }

    List_Program = ["810","830","850"]
    Normal_Title={'ID':'FACILITYNUMBER',
                  'BUSINESS_NAME':'FACILITYNAME',
                  'TYPE':'FACILITYTYPE',
                  'CITY':'CITY',
                  'ADDRESS':'STREETADDRESS',
                  'ZIP':'ZIPCODE',
                  'STATE':'STATE',
                  'PHONE':'TELEPHONE',
                  'CAPACITY':'CAPACITY'}

    try:
        List_Zip_Url=r"C:\Users\MyPC\Desktop\List Zip.csv"
        List_Zip=pandas.read_csv(List_Zip_Url)
    except:pass

    def start_requests(self):
        for Program in self.List_Program:
            for index,Zip_Code in self.List_Zip.iterrows():
                yield scrapy.Request(url=self.Main_Url.format(Program,Zip_Code['ZIP']),callback=self.parse,dont_filter=True)

    def parse(self, response):
        Json_Dict = json.loads(response.text)

        for Record in Json_Dict['FACILITYARRAY']:
            yield scrapy.Request(url=self.Detail_Url.format(Record['FACILITYNUMBER']),dont_filter=True,callback=self.parse_detail)

    def parse_detail(self,response):
        Json_Dict=json.loads(response.text)
        Detail_Dict=Json_Dict['FacilityDetail']
        Temp_Dict=dict()

        for title,selector in self.Normal_Title.items():
            Temp_Dict[title]=Detail_Dict[selector]

        yield Temp_Dict



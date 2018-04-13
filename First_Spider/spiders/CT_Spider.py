import scrapy
import regex
import json
import unicodedata
import pandas

class AgeServed():
    limitation={'week':8,'month':96}
    def __init__(self,week_line):
        self.week_line=week_line
    def __str__(self):
        if self.week_line<self.limitation['week']:return "{0} week(s)".format(self.week_line)
        if self.week_line<self.limitation['month']:return  "{0} month(s)".format(self.week_line//4)
        return "{0} year(s)".format(self.week_line//48)

class QuotesSpider(scrapy.Spider):
    name = "CT_Spider"
    Main_Url="http://search.211childcare.org/providers.json?location[]={0}&location[]={1}&proximity=5"
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

    Filter_Cat=['Family Child Care','Child Care Center']
    Normal_Title={'ID':'id','BUSINESS_NAME':'business_name','FIRST_NAME':'first_name','LAST_NAME':'last_name','TYPE':'type_of_care',
                  'CITY':'city','ADDRESS':'address','ZIP':'zip','STATE':'state',
                  'PHONE':'phone_number','WEBSITE':'website','CAPACITY':'capacity'}

    def start_requests(self):
        for index,city in self.List_Zip.iterrows():
            yield scrapy.Request(url=self.Main_Url.format(city['LAT'],city['LONG']),callback=self.parse,dont_filter=True)

    def parse(self, response):
        Result_List=json.loads(response.text)

        for record in Result_List:
            if record['type_of_care'] not in self.Filter_Cat:continue
            Temp_Dict = dict()
            for field in self.Normal_Title.keys():
                Temp_Dict[field]=record[self.Normal_Title[field]]

            try:
                Temp_Dict['AGE_SERVED']="{0} to {1}".format(str(AgeServed(record['age_range_min'])),str(AgeServed(record['age_range_max'])))
            except:pass

            List_Rate=record['shifts'][0]['rates_by_age']
            if List_Rate!=None:
                for Rate_Record in List_Rate:
                    for key,value in Rate_Record['rates'].items():
                        if value!=None:
                            try:
                                Temp_Dict["{0} {1}".format(Rate_Record['group'],key)]=value
                            except:break
            yield Temp_Dict
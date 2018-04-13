import scrapy
import json
import regex
import pandas

class QuotesSpider(scrapy.Spider):
    name = "FL_Spider"

    Main_Url=r"https://cares.myflfamilies.com/PublicSearch/Search"

    Filter_Field='ID'

    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        },
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200
        },

    }

    Bound_Value='0912877511'
    PayLoad='-----------------------------{0}\nContent-Disposition: form-data; name="dcfSearchBox"\n\n{1}\n-----------------------------{0}--'
    HeadContent={'Content-Type': 'multipart/form-data; boundary=---------------------------{0}'.format(Bound_Value)}

    Normal_Title={'ID':'ProviderID',
                  'BUSINESS_NAME':'Name',
                  'TYPE':'ProgramType',
                  'CITY':'City',
                  'COUNTY': 'County',
                  'ADDRESS':'FullAddress',
                  'ZIP':'ZipCode',
                  'STATE':'State',
                  'PHONE':'PhoneNumber',
                  'CAPACITY':'Capacity'}

    try:
        List_Zip_Url=r"C:\Users\MyPC\Desktop\List Zip.csv"
        List_Zip=pandas.read_csv(List_Zip_Url)
    except:pass

    def start_requests(self):
        for index,Zip_Code in self.List_Zip.iterrows():
            yield scrapy.Request(url=self.Main_Url,method='POST',headers=self.HeadContent,body=self.PayLoad.format(self.Bound_Value,Zip_Code['ZIP']),callback=self.parse,dont_filter=True)

    def parse(self, response):
        Script_Collection=response.css('script::text').extract()
        Define_Script=regex.compile(r'kendoGrid\(\{',regex.IGNORECASE)

        for Script in Script_Collection:
            if Define_Script.search(Script):break

        Get_Data = regex.compile(r'(?<=data":\{"Data":).*?\}\}\]', regex.IGNORECASE)

        if not Get_Data.search(Script):return

        Json_String=Get_Data.search(Script).group()
        Json_List=json.loads(Json_String)

        if len(Json_List)==0:return

        for Record in Json_List:
            Info_Dict=Record['Provider']

            Temp_Dict=dict()
            for Title,Selector in self.Normal_Title.items():
                Temp_Dict[Title]=Info_Dict[Selector]

            yield Temp_Dict
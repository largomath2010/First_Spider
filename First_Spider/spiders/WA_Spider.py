import scrapy
import regex
from bs4 import BeautifulSoup
import json

class QuotesSpider(scrapy.Spider):
    name = "WA_Spider"

    start_urls = [r"https://www.findchildcarewa.org/PSS_Search?ft=Child%20Care%20Center;Family%20Child%20Care%20Home&p=DEL%20Licensed;Unlicensed%20Facility&PSL-0030=Open"]
    Json_Url = r"https://www.findchildcarewa.org/apexremote"
    Detail_Url = r"https://www.findchildcarewa.org/PSS_Provider?id={0}"

    Filter_Field='ID'

    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        },
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200,
        },
        'ROBOTSTXT_OBEY':False,
    }

    Is_Script_Token = regex.compile(r'\"PSS_SearchController\"', regex.IGNORECASE)
    Get_Token_Dict = regex.compile(r'\{\"PSS_SearchController\".*?\}\}', regex.IGNORECASE)
    Get_City=regex.compile('.*?(?=,)',regex.IGNORECASE)
    Get_State = regex.compile('(?<=,\s+)\S.*?\S+(?=\s+)', regex.IGNORECASE)
    Get_Code = regex.compile('(?<=\s+)\d.*?$', regex.IGNORECASE)
    Get_Title=regex.compile(r'.*?(?=:|$)',regex.IGNORECASE)
    Get_Phone = regex.compile(r'^.*?(?=\d/|$)', regex.IGNORECASE)
    Fetch_Json = {"action": "PSS_SearchController", "method": "getKeys","type": "rpc", "tid": 2,
                  "data": ["", "'Child Care Center','Family Child Care Home'", ["DEL Licensed", "Unlicensed Facility"],
                           None, None, None, ["(Provider_Status_External__c='Open')"]],
                  "ctx": {"csrf": "", "vid": "066t0000000Cg99", "ns": "", "ver": 39}}
    Head_Content = {'X-User-Agent': 'Visualforce-Remoting', 'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': r'https://www.findchildcarewa.org/PSS_Search?ft=Child%20Care%20Center;Family%20Child%20Care%20Home&p=DEL%20Licensed;Unlicensed%20Facility&PSL-0030=Open',
                    'Host': 'www.findchildcarewa.org'}

    def parse(self,response):
        Script_Collection = response.css('script::text').extract()
        for Script in Script_Collection:
            if self.Is_Script_Token.search(Script):break

        Token_Dict = json.loads(self.Get_Token_Dict.search(Script).group())
        self.Fetch_Json['ctx']['csrf'] = Token_Dict['PSS_SearchController']['ms'][0]['csrf']
        return scrapy.Request(url=self.Json_Url,method='POST',headers=self.Head_Content,body=json.dumps(self.Fetch_Json),callback=self.parse_general)

    def parse_general(self,response):
        List_ID = json.loads(response.text)[0]['result']

        for ID in List_ID:
            yield scrapy.Request(url=self.Detail_Url.format(ID), callback=self.parse_detail,meta={'ID':ID},dont_filter=True)

    def parse_detail(self,response):

        Title_Collection = response.css('div.col-md-6>div>label').extract()
        Value_Collection = response.css('div.col-md-6>div>div>p').extract()
        Temp_Dict=dict()

        Temp_Dict['ID']=response.meta.get('ID')
        Temp_Dict['BUSINESS_NAME'] = response.css('.col-md-8>h1::text').extract_first()

        try:
            Temp_Dict['PHONE'] = self.Get_Phone.search(response.css('.col-xs-4 > p:nth-child(2)::text').extract_first()).group()
        except:pass

        Address_List = response.css('.col-xs-4>p:first-child::text').extract()

        for Address in Address_List:
            State_Check = self.Get_State.search(Address)
            Zip_Check = self.Get_Code.search(Address)
            City_Check = self.Get_City.search(Address)
            if State_Check and Zip_Check:
                Temp_Dict['CITY'] = City_Check.group()
                Temp_Dict['STATE'] = State_Check.group()
                Temp_Dict['ZIP'] = Zip_Check.group()
            else:
                Temp_Dict['ADDRESS'] = Address

        for Title_Tag, Value_Tag in zip(Title_Collection, Value_Collection):
            Title = self.Get_Title.search(BeautifulSoup(Title_Tag, 'html.parser').text).group()
            Value = BeautifulSoup(Value_Tag, 'html.parser').text
            Temp_Dict[Title] = Value

        yield Temp_Dict



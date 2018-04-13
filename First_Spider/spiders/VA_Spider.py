import scrapy
import regex
from bs4 import BeautifulSoup

class QuotesSpider(scrapy.Spider):
    name = "VA_Spider"

    start_urls = [r"http://www.dss.virginia.gov/facility/search/cc2.cgi?rm=Search;"]
    Detail_URL = r"http://www.dss.virginia.gov/facility/search/cc2.cgi?rm=Details;ID={0};"

    Filter_Field='ID'

    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        },
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200
        },

    }

    Get_Text_Only=regex.compile(r'(?<=^|\n\s*)\S.*?\S?(?=\s*\n|$)',regex.IGNORECASE)
    Get_ID = regex.compile(r'(?<=Details;ID=)\d+(?=;)', regex.IGNORECASE)
    Get_City=regex.compile('.*?(?=,)',regex.IGNORECASE)
    Get_State = regex.compile('(?<=,\s+)\S.*?\S+(?=\s+)', regex.IGNORECASE)
    Get_Code = regex.compile('(?<=\s+)\d.*?$', regex.IGNORECASE)
    Get_Title=regex.compile(r'.*?(?=:|$)',regex.IGNORECASE)

    def parse(self, response):
        List_Detail=response.css('a[target="_blank"]::attr(href)').extract()
        for Detail in List_Detail:
            ID_Test=self.Get_ID.search(Detail)
            if ID_Test:
                Id=ID_Test.group()
                yield scrapy.Request(url=self.Detail_URL.format(Id),callback=self.parse_detail,meta={'Id':Id},dont_filter=True)

    def parse_detail(self,response):
        Temp_Dict=dict()
        Id=response.meta.get('Id')
        Temp_Dict['ID']=Id

        Main_Collection=response.css('td[colspan="2"]').extract()
        for Line in Main_Collection:
            Soup=BeautifulSoup(Line,'html.parser')
            if not Soup.table:
                List_Text=self.Get_Text_Only.findall(Soup.text)
                if len(List_Text)!=1:
                    Temp_Dict['BUSINESS_NAME']=List_Text[0]
                    Address = 'ADDRESS_{0}'
                    for i in range(len(List_Text)):
                        if i==0:continue
                        Temp_Dict[Address.format(str(i))]=List_Text[i]
                elif self.Get_State.search(Soup.text):
                    Temp_Dict['STATE']=self.Get_State.search(List_Text[0]).group()
                    Temp_Dict['CITY'] = self.Get_City.search(List_Text[0]).group()
                    Temp_Dict['ZIP_CODE'] = self.Get_Code.search(List_Text[0]).group()
                else:
                    Temp_Dict['PHONE']=List_Text[0]

        Soup=BeautifulSoup(response.css('table.cc_search:not([border])').extract_first(),'html.parser')
        Sub_Collection=Soup.findAll('tr')

        for Tr_Elem in Sub_Collection:
            Td_Collection=Tr_Elem.findAll('td')
            Title=self.Get_Title.search(self.Get_Text_Only.search(Td_Collection[0].text).group()).group()
            Field_List=self.Get_Text_Only.findall(Td_Collection[1].text)
            Field=""

            for Text in Field_List:
                if Field=="":Field=Field+Text
                else:Field=Field+" "+Text

            Temp_Dict[Title]=Field
        yield Temp_Dict



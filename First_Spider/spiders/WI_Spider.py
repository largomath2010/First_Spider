import scrapy
import regex
from bs4 import BeautifulSoup
import urllib
import os
import pandas

class QuotesSpider(scrapy.Spider):
    name = "WI_Spider"

    Filter_Field='URL'

    Main_Url = r"https://childcarefinder.wisconsin.gov/Search/SearchResults.aspx?q=16-0B-6B-0B:MHwwfHx8fHx8MHxUcnVlfFRydWV8VHJ1ZXxUcnVlfFRydWV8VHJ1ZXxUcnVlfFRydWV8VHJ1ZXxGYWxzZXxUcnVlfFRydWV8VHJ1ZXxUcnVlfFRydWV8VHJ1ZXwtMXwtMXxGYWxzZXw1fGJ8MHwwfHxkfEZhbHNlfDB8RmFsc2U="
    Domain_Url = r"https://childcarefinder.wisconsin.gov/{0}"
    start_urls=[Main_Url]

    Params = "__EVENTTARGET=ctl00%24BodyCPH%24gvSearchResults%24ctl01%24pagerControl1%24lbNext&__VIEWSTATE={0}&__VIEWSTATEGENERATOR={1}&__EVENTVALIDATION={2}&ctl00%24SkinChooser=Bootstrap"
    Header = {'Content-Type': 'application/x-www-form-urlencoded'}

    Normal_Title_List={'AGE_SERVED':'#ProviderDetails_AgesServed::text','PHONE':'#ProviderDetails_ContactPhone>a::text','CONTACT_NAME':'#ProviderDetails_ContactName::text','BUSINESS_CORP':'div.col-sm-5>div.row>div.Bold::text','LICENSEE':'#ProviderDetails_LicenseeName::text'}

    Get_Text = regex.compile(r'(?<=\n\s*?)\S.*?\S?(?=\s*?\n)', regex.IGNORECASE)
    Get_ID=regex.compile(r'(?<=ProviderNumber=)\d*?(?=\D)',regex.IGNORECASE)
    Get_Sharp_Title = regex.compile(r'(?<=\n\s*?)\S.*?\S?(?=\s*?#\s*?\n)', regex.IGNORECASE)
    Get_Parent_Path=regex.compile(r'^.*?\\(?=[^\\]*?\\[^\\]*?$)',regex.IGNORECASE)

    Existing_List=[]
    try:
        Existing_Data_URL=Get_Parent_Path.search(os.path.realpath(__file__)).group()+"Data.csv"
        Existing_Data=pandas.read_csv(Existing_Data_URL)
        Existing_List=Existing_Data[Filter_Field].tolist()
        List_Proxy_Url=Get_Parent_Path.search(os.path.realpath(__file__)).group()+"List_Proxy.txt"
    except:pass

    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        },
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200,
            'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
            'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
        },
        'ROBOTSTXT_OBEY': False,
        'ROTATING_PROXY_LIST_PATH': List_Proxy_Url,
    }

    def Try_Assign(self, Regex_Expression, Search_String, Orientaton="Search", Pos=0):
        if Regex_Expression.search(Search_String):
            if Orientaton == "Search":
                return Regex_Expression.search(Search_String).group()
            elif Orientaton == "Findall" and Pos + 1 <= len(Regex_Expression.findall(Search_String)):
                return Regex_Expression.findall(Search_String)[Pos]
        return None

    def parse(self,response):
        Row_Collection = response.css('#ctl00_BodyCPH_gvSearchResults>tbody>tr').extract()
        self.log('Moving to next site')
        if len(Row_Collection)==0:return
        for Row in Row_Collection:
            Soup = BeautifulSoup(Row, 'html.parser')
            Detail_Url = self.Domain_Url.format(Soup.a['href'])
            if Detail_Url in self.Existing_List:continue
            Temp_Dict = dict()
            Col_Collection = Soup.findAll('td')
            if len(Col_Collection) < 5: continue

            Temp_Dict['BUSINESS_NAME'] = self.Try_Assign(self.Get_Text,Col_Collection[2].text)
            Temp_Dict['CARE_TYPE'] = self.Try_Assign(self.Get_Text,Col_Collection[1].text)
            Temp_Dict['URL']=Detail_Url

            List_Address = self.Get_Text.findall(Col_Collection[4].text)
            List_Length = len(List_Address)
            Temp_Dict['ADDRESS'] = ', '.join(List_Address[:List_Length - 3])
            Temp_Dict['CITY'] = List_Address[List_Length - 3]
            Temp_Dict['STATE'] = List_Address[List_Length - 2]
            Temp_Dict['ZIP'] = List_Address[List_Length - 1]
            yield scrapy.Request(url=Detail_Url,meta={'Temp_Dict':Temp_Dict},callback=self.parse_detail)

        Viewstate_Token = urllib.parse.quote_plus(response.css('#__VIEWSTATE::attr(value)').extract_first())
        Viewstate_Generator = urllib.parse.quote_plus(response.css('#__VIEWSTATEGENERATOR::attr(value)').extract_first())
        Viewstate_Validation = urllib.parse.quote_plus(response.css('#__EVENTVALIDATION::attr(value)').extract_first())
        Data = self.Params.format(Viewstate_Token, Viewstate_Generator, Viewstate_Validation)

        yield scrapy.Request(url=self.Main_Url,method='POST',body=Data,headers=self.Header,callback=self.parse)

    def parse_detail(self,response):
        Temp_Dict=response.meta.get('Temp_Dict')
        for Title,Selector in self.Normal_Title_List.items():
            Text=response.css(Selector).extract_first()
            try:
                Temp_Dict[Title]=self.Get_Text.search(Text).group()
            except:Temp_Dict[Title]=Text

        Row_Collection = response.css('div.col-sm-7>div.row').extract()
        for Row in Row_Collection:
            Soup=BeautifulSoup(Row,'html.parser')
            Title=self.Get_Sharp_Title.search(Soup.text)
            if Title:Temp_Dict[Title.group()]=self.Try_Assign(self.Get_Text,Soup.text,"Findall",1)

        Row_Collection = response.css('#divSingleHoursOfOperation>div>div.row').extract()
        if len(Row_Collection)>0:
            Last_Pos = len(Row_Collection) - 1
            Temp_Dict['HOURS'] = ""
            Keep_Houring = True

            while Keep_Houring:
                Soup = BeautifulSoup(Row_Collection[Last_Pos], 'html.parser')
                Hour_String_List = self.Get_Text.findall(Soup.div.text)
                if Hour_String_List[0] == 'Hours':
                    New_Hour = ":".join(Hour_String_List[1:])
                    Keep_Houring = False
                else:
                    New_Hour = ":".join(Hour_String_List)
                    Last_Pos = Last_Pos - 1
                Temp_Dict['HOURS'] = New_Hour if Temp_Dict['HOURS'] == "" else ", ".join([New_Hour, Temp_Dict['HOURS']])

            for i in range(Last_Pos):
                Soup = BeautifulSoup(Row_Collection[i], 'html.parser')
                Field_String_List = self.Get_Text.findall(Soup.div.text)
                Temp_Dict[Field_String_List[0]] = " ".join(Field_String_List[1:])

        Row_Collection = response.css('#divMultipleHoursOfOperation>div>div>div.col-xs-6:not(.Bold)').extract()
        if len(Row_Collection)>0:
            List_Prefix=[self.Get_Text.search(x).group() for x in response.css('#divMultipleHoursOfOperation>div>div>div.Bold.col-xs-6::text').extract()]
            for index,Row in enumerate(Row_Collection):
                Soup=BeautifulSoup(Row,'html.parser')
                Field_String_List=self.Get_Text.findall(Soup.div.text)
                Temp_Dict[List_Prefix[index%2]+" "+Field_String_List[0]]=" ".join(Field_String_List[1:])

            Table_Collection=response.css('.table-striped>tr').extract()
            for Prefix in List_Prefix:
                Temp_Dict[Prefix+"_HOURS"]=""
            for Row in Table_Collection:
                Soup=BeautifulSoup(Row,'html.parser')
                Field_String_List=self.Get_Text.findall(Soup.text)
                for index,Prefix in enumerate(List_Prefix):
                    try:
                        New_Hour=Field_String_List[0]+":"+Field_String_List[index+1]
                        Temp_Dict[Prefix+"_HOURS"]=New_Hour if Temp_Dict[Prefix+"_HOURS"]=="" else ", ".join([Temp_Dict[Prefix+"_HOURS"],New_Hour])
                    except:continue

        yield Temp_Dict


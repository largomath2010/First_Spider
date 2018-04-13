import scrapy
import regex
from bs4 import BeautifulSoup
import urllib
import pandas

class QuotesSpider(scrapy.Spider):
    name = "CO_Spider"

    Search_Url = r"http://www.coloradoshines.com/search?location={0}"
    Main_Url = r"http://www.coloradoshines.com/search"
    Detail_Url = r"http://www.coloradoshines.com/program_details?id={0}"

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

    Get_ID = regex.compile(r'(?<=id=).*?$', regex.IGNORECASE)
    Get_Text = regex.compile(r'(?<=\n\s*)\S.*?\S?(?=\n)', regex.IGNORECASE)
    Get_Title = regex.compile(r'(^|\n).*?(?=:\s?)', regex.IGNORECASE)
    Get_Address = regex.compile('(?<=^|\n).*?(?=,)', regex.IGNORECASE)
    Get_City = regex.compile(r'(?<=,\s*?)\S.*?\S?(?=,)', regex.IGNORECASE)
    Get_State = regex.compile(r'(?<=,\s*?)\S[^,]*?[^,\s](?=\s+\d+)', regex.IGNORECASE)
    Get_Code = regex.compile(r'(?<=\s*?)\d+$', regex.IGNORECASE)
    Get_Rating=regex.compile(r'(?<=rating-)\d*?$',regex.IGNORECASE)

    Params = "page%3AsearchForm=page%3AsearchForm&page%3AsearchForm%3Aj_id120%3A1%3Aj_id128=page%3AsearchForm%3Aj_id120%3A1%3Aj_id128&pagenumber={0}&com.salesforce.visualforce.ViewState={1}&com.salesforce.visualforce.ViewStateVersion={2}&com.salesforce.visualforce.ViewStateMAC={3}"
    Header ={'Content-Type': 'application/x-www-form-urlencoded', 'Host': 'www.coloradoshines.com'}

    try:
        List_Zip_Url=r"C:\Users\MyPC\Desktop\List ZIP.csv"
        List_Zip=pandas.read_csv(List_Zip_Url)
    except:pass

    def Filter_Text_From_Collection(self, Text_Collection):
        for line in Text_Collection:
            try:
                return self.Get_Text.search(line).group()
            except:
                continue
        return None

    def Try_Assign(self,Regex_Expression,Search_String,Orientaton="Search",Pos=0):
        if Regex_Expression.search(Search_String):
            if Orientaton=="Search":return Regex_Expression.search(Search_String).group()
            elif Orientaton=="Findall" and Pos+1<=len(Regex_Expression.findall(Search_String)):return Regex_Expression.findall(Search_String)[Pos]
        return None

    def start_requests(self):
        for index,Line in self.List_Zip.iterrows():
            yield scrapy.Request(url=self.Search_Url.format(Line['ZIP']),callback=self.parse,meta={'Referer':self.Search_Url.format(Line['ZIP'])})

    def parse(self,response):
        Current_Page=response.meta.get('Current_Page')
        Referer = response.meta.get('Referer')
        Viewstate_Token=response.meta.get('Viewstate_Token')
        Viewstate_Version = response.meta.get('Viewstate_Version')
        Viewstate_MAC = response.meta.get('Viewstate_MAC')
        self.Header['Referer']=Referer

        if not Current_Page:
            Current_Page=1
            Viewstate_Token = urllib.parse.quote_plus(response.css('input[id="com.salesforce.visualforce.ViewState"]::attr(value)').extract_first())
            Viewstate_Version = urllib.parse.quote_plus(response.css('input[id="com.salesforce.visualforce.ViewStateVersion"]::attr(value)').extract_first())
            Viewstate_MAC = urllib.parse.quote_plus(response.css('input[id="com.salesforce.visualforce.ViewStateMAC"]::attr(value)').extract_first())

        ID_Collection = response.css('.view-details::attr(href)').extract()
        if len(ID_Collection)==0:return

        for ID in ID_Collection:
            ID_Num=self.Get_ID.search(ID).group()
            yield scrapy.Request(url=self.Detail_Url.format(ID_Num),meta={'ID_Num':ID_Num},callback=self.parse_detail)

        Next_String=response.css('ul.pagination>li.next').extract_first()
        if Next_String:
            Current_Page=Current_Page+1
            yield scrapy.Request(url=self.Main_Url,method='POST',headers=self.Header,callback=self.parse,
                                 body=self.Params.format(str(Current_Page),Viewstate_Token,Viewstate_Version,Viewstate_MAC),
                                 meta={'Current_Page':Current_Page,'Referer':Referer,
                                        'Viewstate_Token':Viewstate_Token,'Viewstate_Version':Viewstate_Version,'Viewstate_MAC':Viewstate_MAC
                                        }
                                 )

    def parse_detail(self,response):
        Temp_Dict=dict()
        Whole_Address = response.css('.field-address::text').extract_first()
        ID_Num=response.meta.get('ID_Num')
        Rate_String = response.css('p.result-rating>span>span::attr(class)').extract_first()

        if Rate_String:Temp_Dict['QUALITY_RATING']=self.Try_Assign(self.Get_Rating,Rate_String)
        
        Temp_Dict['ID']=ID_Num
        Temp_Dict['URL']=self.Detail_Url.format(ID_Num)
        Temp_Dict['ADDRESS']=self.Try_Assign(self.Get_Address,Whole_Address)
        Temp_Dict['CITY'] = self.Try_Assign(self.Get_City,Whole_Address)
        Temp_Dict['STATE'] = self.Try_Assign(self.Get_State,Whole_Address)
        Temp_Dict['ZIP'] = self.Try_Assign(self.Get_Code,Whole_Address)
        Temp_Dict['PHONE'] = response.css('.field-phone>a::text').extract_first()
        Temp_Dict['WEBSITE'] = response.css('.field-website>span>a::text').extract_first()
        Temp_Dict['BUSINESS_NAME']=response.css('.right-content>h1::text').extract_first()

        Collection = response.css('.field-name-field-care>p::text').extract()
        Temp_Dict['CARE_SETTING']=self.Filter_Text_From_Collection(Collection)

        Collection = response.css('.field-name-field-age>p::text').extract()
        Temp_Dict['AGES'] = self.Filter_Text_From_Collection(Collection)

        Collection = response.css('.field-name-field-info>p').extract()

        for Field in Collection:
            Soup = BeautifulSoup(Field, 'html.parser')
            Title = self.Try_Assign(self.Get_Title,self.Try_Assign(self.Get_Text,Soup.text,"Findall"))
            Value = self.Try_Assign(self.Get_Text,Soup.text,"Findall",1)
            Temp_Dict[Title] = Value

        yield Temp_Dict


import scrapy
import regex
from bs4 import BeautifulSoup
import urllib
import pandas

class QuotesSpider(scrapy.Spider):
    name = "ML_Spider"
    Filter_Field='ID'

    Main_Url = r"http://www.checkccmd.org/SearchResults.aspx?ft=&fn=&sn=&z={0}&c=&"
    Domain = r"http://www.checkccmd.org/{0}"

    Params = "__EVENTTARGET=ctl00%24MainContent%24grdResults&__EVENTARGUMENT=Page%24{0}&__VIEWSTATE={1}&__VIEWSTATEGENERATOR={2}&__EVENTVALIDATION={3}"
    Header = {'Content-Type': 'application/x-www-form-urlencoded'}

    Title_List = {'PROVIDER_STATUS': '#ctl00_MainContent_txtProviderStatus::text',
                  'CAPACITY': '#ctl00_MainContent_txtCapacity::text',
                  'APPROVAL_EDUCATION_PROGRAM': '#ctl00_MainContent_txtApprovedEducationProgram::text',
                  'ACCREDITATION': '#ctl00_MainContent_txtAccreditation::text',
                  'PHONE': '#ctl00_MainContent_txtPhone::text',
                  'EMAIL': '#ctl00_MainContent_txtEmail::text',
                  'APPROVAL_FOR': '#ctl00_MainContent_txtHours::text',
                  'LEVEL':'#ctl00_MainContent_txtEXCELSLevel::text'}
    Special_Title = {'CAPACITY': ['CAPACITY', 'AGES']}

    custom_settings = {
        #'ITEM_PIPELINES': {
        #    'First_Spider.pipelines.DuplicatesPipeline': 100
        #},
        'DOWNLOADER_MIDDLEWARES': {
            'First_Spider.middlewares.More_Error_Logged': 200,
        },
        'ROBOTSTXT_OBEY':False,
    }

    Get_ID = regex.compile(r'(?<=fi=)\d*?$', regex.IGNORECASE)
    Get_State = regex.compile(r'(?<=,\s*?)\S\S*?(?=\s*?\S*?$)', regex.IGNORECASE)
    Get_Zip = regex.compile(r'\d*?$', regex.IGNORECASE)
    Get_City = regex.compile(r'(?<=,\s*?)\S[^,]*?(?=\s*?,\s*?[^,]*?$)', regex.IGNORECASE)
    Get_Address = regex.compile(r'^.*?(?=,[^,]*?,[^,]*?$)', regex.IGNORECASE)

    try:
        List_Zip_Url=r"C:\Users\Admin\Desktop\LIST ZIP.csv"
        List_Zip=pandas.read_csv(List_Zip_Url)
    except:pass

    def Try_Assign(self,Regex_Expression,Search_String,Orientaton="Search",Pos=0):
        if Regex_Expression.search(Search_String):
            if Orientaton=="Search":return Regex_Expression.search(Search_String).group()
            elif Orientaton=="Findall" and Pos+1<=len(Regex_Expression.findall(Search_String)):return Regex_Expression.findall(Search_String)[Pos]
        return None

    def start_requests(self):
        for index,Line in self.List_Zip.iterrows():
            yield scrapy.Request(url=self.Main_Url.format(Line['ZIP']),callback=self.parse,meta={'Referer':self.Main_Url.format(Line['ZIP'])})


    def parse(self,response):
        Current_Page=response.meta.get('Current_Page')
        Referer=response.meta.get('Referer')
        if not Current_Page: Current_Page = 1

        Viewstate_Token = urllib.parse.quote_plus(response.css('input#__VIEWSTATE::attr(value)').extract_first())
        Viewstate_Generator = urllib.parse.quote_plus(response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first())
        Viewstate_Validation = urllib.parse.quote_plus(response.css('input#__EVENTVALIDATION::attr(value)').extract_first())

        Link_Collection = response.css('table#ctl00_MainContent_grdResults>tr[bgcolor]>td>font>a::attr(href)').extract()
        Row_Collection = response.css('table#ctl00_MainContent_grdResults>tr[bgcolor]').extract()

        for Link, Row in zip(Link_Collection, Row_Collection):
            Temp_Dict = dict()
            Temp_Dict['URL'] = self.Domain.format(Link)
            Temp_Dict['ID'] = self.Get_ID.search(Link).group()

            Soup = BeautifulSoup(Row, 'html.parser')
            List_Results = Soup.findAll('td')

            Temp_Dict['BUSINESS_NAME'] = List_Results[0].text
            Temp_Dict['COUNTY'] = List_Results[3].text
            Temp_Dict['PROGRAM_TYPE'] = List_Results[5].text

            Whole_Address = List_Results[2].text
            Temp_Dict['ADDRESS'] = self.Try_Assign(self.Get_Address, Whole_Address)
            Temp_Dict['CITY'] = self.Try_Assign(self.Get_City, Whole_Address)
            Temp_Dict['ZIP_CODE'] = self.Try_Assign(self.Get_Zip, Whole_Address)
            Temp_Dict['STATE'] = self.Try_Assign(self.Get_State, Whole_Address)
            yield scrapy.Request(url=self.Domain.format(Link), meta={'Temp_Dict': Temp_Dict},
                                 callback=self.parse_detail)

        if len(Link_Collection)!=0:
            Current_Page=Current_Page+1
            yield scrapy.Request(url=Referer,method='POST',headers=self.Header,
                                 body=self.Params.format(Current_Page,Viewstate_Token,Viewstate_Generator,Viewstate_Validation),
                                 meta={'Current_Page':Current_Page,'Referer':Referer})

    def parse_detail(self,response):
        Temp_Dict=response.meta.get('Temp_Dict')

        for title, css_selector in self.Title_List.items():
            Scraping_List = response.css(css_selector).extract()
            if len(Scraping_List) == 1:
                Temp_Dict[title] = Scraping_List[0]
            elif len(Scraping_List) > 1:
                if title in self.Special_Title.keys():
                    Temp_Dict[self.Special_Title[title][0]] = Scraping_List[0]
                    Temp_Dict[self.Special_Title[title][1]] = ", ".join(Scraping_List[1:len(Scraping_List)])
                else:
                    Temp_Dict[title] = ", ".join(Scraping_List)

        yield Temp_Dict



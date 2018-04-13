import scrapy
import regex
from bs4 import BeautifulSoup
import unicodedata

def Collection_Index(Temp_Col,Temp_String):
    re=regex.compile(r"{0}".format(Temp_String),regex.IGNORECASE)
    for i in range(len(Temp_Col)):
        if re.search(Temp_Col[i].extract()):
            return i
    return None

def Get_Text_From_CSS_Item(HTML_ELEM):
    Soup=BeautifulSoup(HTML_ELEM.extract(),'html.parser')
    return unicodedata.normalize("NFKD",Soup.text)

class QuotesSpider(scrapy.Spider):
    name = "Idaho_Spider"
    State_Zip = "83"
    Filter_Field='URL'
    custom_settings = {
        'ITEM_PIPELINES': {
            'First_Spider.pipelines.DuplicatesPipeline': 100
        }
    }

    start_urls=["https://orm.naccrraware.net/orm/ormHome.action?uid=3TVVX8B2XOU9NXF"]
    search_url="https://orm.naccrraware.net/orm/ormDoSearch.action"
    main_url="https://orm.naccrraware.net/orm/ormShowProviderDetail.action?id="

    fetch_data={'advSearch':'1','City':'','login':'true','page':'search','TypeOfCare':['Child Care Center','Family Child Care','(FCC)Group Child Care'],'userReferalCount':'0','userSearchCount':'0'}

    List_Title_Single=['Business Name','Type Of Care','Age Range For Care']
    List_Title_Complex = {'Street Address':{'Zip':['Address','Zip Code']}, 'City':{'Website':['City','Website']}, 'Area Code':{'Phone':['Area Code','Tel Number']} }

    def parse(self, response):
        Temp_List=response.request.headers['Cookie'].decode('ascii').split(";")
        Temp_Cook=dict()
        feeder=self.fetch_data

        for item in Temp_List:
            Cookie_Element=item.split("=")
            Temp_Cook[Cookie_Element[0]]=Cookie_Element[1]

        Temp_City=response.css('select#City').extract_first()
        Soup=BeautifulSoup(Temp_City,'html.parser')
        Temp_List=unicodedata.normalize("NFKD",Soup.text.replace(" ","")).split("\n")

        for item in Temp_List:
            feeder['City']=item
            yield scrapy.FormRequest(url=self.search_url,method='POST',cookies=Temp_Cook,formdata=feeder,callback=self.parse_search,meta={'Temp_Cook':Temp_Cook},dont_filter=True)

    def parse_search(self,response):
        Page=response.meta.get('Page')
        Temp_Cook = response.meta.get('Temp_Cook')
        if Page==None:Page=1
        Page+=1


        html_ids=response.css('a.pageLink::attr(onclick)')
        if len(html_ids)==0:return

        re=regex.compile(r"(?<=\()(\d)*(?=\))",regex.IGNORECASE)

        for item in html_ids:
            page_id=re.search(item.extract()).group()
            yield scrapy.Request(url=self.main_url+page_id,cookies=Temp_Cook,callback=self.parse_detail,dont_filter=True)


        yield scrapy.FormRequest(url=self.search_url,method='POST',cookies=Temp_Cook,formdata={'pageNum':str(Page+1)},callback=self.parse_search,meta={'Temp_Cook':Temp_Cook,'Page':Page},dont_filter=True)

    def parse_detail(self,response):
        re = regex.compile(r"(?<=(zip)).*", regex.IGNORECASE)
        htmlresults=response.css('td.resultsCell')
        htmllabels=response.css('td.detailLabelCell')
        num_item=len(htmlresults)
        Zip_Index = Collection_Index(htmllabels, "Street Address")

        if num_item==0:return
        if Zip_Index==None:return

        State = unicodedata.normalize("NFKD", BeautifulSoup(htmlresults[Zip_Index].extract(), 'html.parser').text)
        State=re.search(State).group().replace(" ","")

        if regex.search(r"^{0}".format(self.State_Zip),State,regex.IGNORECASE):
            Temp_Dict=dict()
            Temp_Dict['URL'] = response.request.url

            for i in range(num_item):
                Label_Text=unicodedata.normalize("NFKD",BeautifulSoup(htmllabels[i].extract(),'html.parser').text)
                Result_Text = unicodedata.normalize("NFKD", BeautifulSoup(htmlresults[i].extract(), 'html.parser').text)

                for item in self.List_Title_Single:
                    re = regex.compile(r"{0}".format(item), regex.IGNORECASE)
                    if re.search(Label_Text):
                        Temp_Dict[item]=Result_Text

                for item in self.List_Title_Complex.keys():
                    re = regex.compile(r"{0}".format(item), regex.IGNORECASE)
                    if re.search(Label_Text):
                        Spliter=list(self.List_Title_Complex[item].keys())[0]
                        List_Header=list(self.List_Title_Complex[item].values())[0]

                        re=regex.compile(r"(?<=({0})).*".format(Spliter),regex.IGNORECASE)
                        Temp_Dict[List_Header[1]]=re.search(Result_Text).group()

                        re = regex.compile(r".*(?=({0}))".format(Spliter),regex.IGNORECASE)
                        Temp_Dict[List_Header[0]] = re.search(Result_Text).group()

            htmlfees = response.css('td.careCell')

            if len(htmlfees)>0:
                i=0
                while i<len(htmlfees):
                   Temp_Dict[Get_Text_From_CSS_Item(htmlfees[i])]=Get_Text_From_CSS_Item(htmlfees[i+1])
                   i=i+2

            yield Temp_Dict




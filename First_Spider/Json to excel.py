import json
import pandas
import regex

json_url=r"I:\Linh Tinh\Python\First_Spider\ML_Data.json"
GET_NUMBER=regex.compile(r"[-+]?\d*\.\d+",regex.IGNORECASE)
GET_TYPE=regex.compile(r"(?<=[-+]?\d*\.\d+\s+).*",regex.IGNORECASE)

with open(json_url,"r") as json_file:
    json_string=json_file.read()

json_string=json_string[2:(len(json_string)-2)]
Jsonize=regex.compile(r"\{.*?\}",regex.IGNORECASE)
Temp_List=Jsonize.findall(json_string)
Submit_df=pandas.DataFrame()

for item in Temp_List:
    Temp_Dict=json.loads(item)
    Temp_df = pandas.DataFrame([Temp_Dict], columns=Temp_Dict.keys())
    Submit_df=pandas.concat([Submit_df,Temp_df],ignore_index=True)

Submit_df.to_csv(r"F:\Result.csv")



print(Submit_df)
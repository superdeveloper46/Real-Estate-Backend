from bs4 import BeautifulSoup
import re
import requests
import urllib.parse

class FastPeopleSearch():
    def __init__(self, API_KEY):
        self.API_KEY = API_KEY
        self.escape_words = [
            "Homes, Rental Properties, businesses, apartments, condos and/or other real estate associated",
            "Cell/Mobile/Wireless and/or landline telephone numbers",
            "Alias, Nicknames, alternate spellings, married and/or maiden names",
            "Mother, father, sisters, brothers, spouses ",
            "View Free Details"
       ]

    def toCamel(self, s):
        ret = ''.join(x for x in s.title() if not x.isspace())
        return ret[0].lower() + ret[1:]

    def allowed_value(self, i):
        for escape_word in self.escape_words:
            if escape_word in i:
                return False

        return True

    def splitList(self, l):
        splittedList = []

        for itemIndex in range(len(l)):
            if itemIndex % 2 == 0:
                try:
                    l[itemIndex+1]
                    value = ", ".join([l[itemIndex], l[itemIndex+1]]) 
                except:
                    value = l[itemIndex]
                    

                splittedList.append(value)
        
        return splittedList

    def checkInputs(self, inputs):
        empty_chars = ["", " ", None]
        for input_ in inputs.values():
            if input_ in empty_chars:
                return False

        else:
            return True
      

    def search(self, searchType, inputs):
        """
        name ->  {"full_name": "Ariel Herrera", address:""}
        address ->  { location:""}
        phone ->  { phone:""}
        """

        if searchType == "name":
            is_valid = self.checkInputs(inputs)
            if is_valid:
                url  = "https://www.fastpeoplesearch.com/name/{}_{}".format(
                    inputs["name"].replace(" ","-"),
                    inputs["location"].replace(" ","-")
                    )
            else:
                raise ValueError("Please check the inputs.")
    
        elif searchType == "address":
            is_valid = self.checkInputs(inputs)
            if is_valid:
                url  = "https://www.fastpeoplesearch.com/address/{}_{}".format(inputs["address"].replace(" ","-"), inputs["location"].replace(" ","-"))
            else:
                raise ValueError("Please check the inputs.")

        elif searchType == "phone":
            is_valid = self.checkInputs(inputs)
            if is_valid:
                url  = "https://www.fastpeoplesearch.com/{}".format(inputs["phone"].replace(" ","-").replace(")","").replace("(",""))
            else:
                raise ValueError("Please check the inputs.")

        url = url.lower().replace(",","")
        encodedUrl = urllib.parse.quote(url)


        response = requests.get("http://api.scrape.do?token={}&url={}".format(self.API_KEY, encodedUrl))
        data = self.parser(response.text)
        if response.status_code not in  [200, 201,202,203]:
            print(response.status_code, 'Response HTTP Response Body: ', response.text)
            
        data = self.parser(response.text)
        return data

  
    def parser(self, page_html):
        soup = BeautifulSoup(page_html, "lxml")

        try:
            lat = re.findall(r'"latitude":.*?"(.*?)",', str(soup))[0]
        except:
            lat = None

        try:
            lng = re.findall(r'"longitude":.*?"(.*?)"', str(soup))[0]
        except:
            lng = None

        matches = []
        cards = soup.findAll("div", "card")
        for card in cards:
            if "Frequently Asked Questions" in card.text:
                continue

            data = {
                "fullName":None,
                "location":None ,
                "coordinate_lat":lat,
                "coordinate_lng":lng

            }

            title = card.find("h2", "card-title")
            data["fullName"] = title.find("span", "larger").text.strip().replace("\n","")
            
            try:
                data["location"] = title.find("span", "grey").text.strip().replace("\n","")
            except:
                data["location"] = None

            current_key = None
            for text in card.text.split("\n"):
                if text not in [""]:
                    if text[-1] == ":":
                        current_key = self.toCamel(text.replace(":",""))
                        data[current_key] = []
                    else:
                        if current_key == None:
                            if "age: " in text.lower():
                                data["age"] = text.split(": ")[-1]
                        else:
                            
                            if self.allowed_value(text) and text.strip() != "":
                                data[current_key].append(text.strip().replace("\n",""))



            if "pastAddresses" in list(data.keys()):
                data["pastAddresses"] = self.splitList(data["pastAddresses"])

            data["currentHomeAddress"] = ", ".join(data["currentHomeAddress"])
            matches.append(data)

        return matches
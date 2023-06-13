import gspread
import urllib3
import xmltodict
import json


class XMLToGSpread:
    def __init__(self, file_url, table_name, parse_keywords, worksheet_name="parsed_data", blank_headers=[]):
        self.header = []
        self.content = []
        self.offer_data = {}
        self.header_created = False
        self.table_name = table_name
        self.parse_keywords = parse_keywords
        self.worksheet_name = worksheet_name
        self.blank_headers = blank_headers

        if file_url.find("http") == -1:
            xml_file = open(file_url, encoding="utf8")  # opening source .xml file for reading with utf8 encoding
            xml_tree = xml_file.read()
        else:
            http = urllib3.PoolManager()
            response = http.request("GET", file_url)  # creating GET-request with link file_url
            xml_tree = response.data  # writing response text with XML to the xml_tree
        # convering XML tree to the dict with xmltodict.parse()
        # converting dict to the JSON with json.dumps()
        # and using utf8 encoding to ensure readable result
        parsed_json = json.dumps(xmltodict.parse(xml_tree), ensure_ascii=False).encode("utf8")
        xml_dict = json.loads(parsed_json)  # converting JSON back to the dict
        # taking first key as the root key
        # (?) change it to the config type because of the different styles of XML data construction
        root_key = ''
        for key in xml_dict:
            root_key = key

        root_dict = xml_dict[root_key]
        # skipping unneccessary keys
        # TODO: add list of keys that we should throw away
        for key in root_dict:
            if key.find("@") != -1:
                continue
            if key == "generation-date":
                continue
            if key == "feed_version":
                continue
            self.sort_offers(root_dict[key])

    # this function parses dict offers_list
    def sort_offers(self, offers_list):
        # sorting out information for it futher sending to GSpreads
        for offer in offers_list:
            self.parse_offer(offer)

    # this function sends parsed data to the GSpread
    def send_to_spreads(self):
        print("Sending data to Google Spreadsheets...")
        gc = gspread.service_account()
        sh = gc.open(self.table_name)

        worksheet_id = self.worksheet_name
        # how many columns and rows we need for this data
        rows = len(self.header)
        cols = len(self.content)

        # getting worksheet object or creating it, if it doesn't exist
        try:
            worksheet = sh.add_worksheet(title=worksheet_id, rows=rows, cols=cols)
        except gspread.exceptions.APIError:
            worksheet = sh.worksheet(worksheet_id)

        blank_headers_data = []

        # removing header
        if len(worksheet.row_values(1)) > 0:
            worksheet.delete_row(1)

            # saving previous values that was created manuallly
            iterator = len(self.parse_keywords.keys()) + 1
            for k in range(iterator, iterator + len(self.blank_headers)):
                blank_headers_data.append(worksheet.col_values(k))

        # clearing worksheet
        worksheet.clear()

        # appending header
        worksheet.append_row(self.header)

        # appending our saved information
        for i in range(cols):
            for k in range(len(blank_headers_data)):
                try:
                    self.content[i].append(blank_headers_data[k][i])
                except IndexError:
                    self.content[i].append("")

        # appending all parsed data
        worksheet.append_rows(self.content)

        print("Data was successfully transferred and saved! ({0})".format(self.worksheet_name))

    # this function parses every entry in our list
    def parse_offer(self, offer):
        self.offer_data = {}

        for key in self.parse_keywords:
            # saving current key as sub_key
            sub_key = key
            if key in offer:
                value = offer[sub_key]
            else:
                # if key is not declared in dict keywords_parse then leaving this variable empty
                value = ""

            if type(value) != str:
                parse_info = self.parse_keywords[key]
                if type(parse_info) == str:
                    sub_key = self.parse_keywords[sub_key]
                    value = value[sub_key]
                elif type(parse_info) == dict:
                    self.parse_inner(value, parse_info["content"])
                    self.merge_values(parse_info)
                    value = None
                elif type(parse_info) == list:
                    for item in parse_info:
                        self.parse_inner(value, item["content"])
                        self.merge_values(item)
                    value = None
                elif type(parse_info) == set:
                    new_data = ""
                    for j in self.parse_keywords[sub_key]:
                        new_data = new_data + value[j]
                    value = new_data

            # if our value is not None then adding it's value to the parsed data
            if value is not None:
                self.offer_data[sub_key] = value

        # if the header was not created yet, creating it
        if not self.header_created:
            self.header_created = True
            self.header = list(self.offer_data.keys()) + self.blank_headers

        # append parsed values to the dict
        # print(self.offer_data)
        self.content.append(list(self.offer_data.values()))
    
    # this function performs nested parsing
    def parse_inner(self, data, whitelist):
        if is_key_valid(whitelist, "content"):
            self.parse_inner(data, whitelist["content"])
        else:
            for content_key in whitelist:
                if content_key.find(">") == -1:
                    self.offer_data[content_key] = data[content_key]
                else:
                    deep = content_key.split(">")
                    val = data
                    last_key = deep[len(deep) - 1]
                    for key in deep:
                        val = val[key]

                    if not is_key_valid(self.offer_data, last_key):
                        content_key = last_key

                    self.offer_data[content_key] = val
    
    # this function merges parsed values in one value
    def merge_values(self, parse_info):
        if not is_key_valid(parse_info, "merge"):
            return

        merged_data = ""
        items = parse_info["merge"]["items"]
        for i in range(len(items)):
            merged_data = merged_data + self.offer_data[items[i]]
            del self.offer_data[items[i]]

        self.offer_data[parse_info["merge"]["name"]] = merged_data


def is_key_valid(v_dict, key):
    if key in v_dict:
        return True

    return False

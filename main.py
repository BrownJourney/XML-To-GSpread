from xmltospread import XMLToGSpread

# source XML file destination (example: https://feeds.kortros.ru/ya/?obj=ilove or C://Documents/file.xml)
xml_source_url = ""
# spreadsheets table name
ss_table_name = ""
# worksheet name (if don't have it already, it will be automatically created)
worksheet_name = ""
# entries in the XML that we want to parse
# Examples:
keywords_parse = {
    "@internal-id": True, # single entry parsing
    "floor": True,
    "rooms": True,
    "sales-agent": "phone", # parsing single entry inside an object 
    "area": {"value", "unit"}, # connecting multiple entries together inside an object. For ex. value is "300" and unit is "m". In the result we'll have "300m"
    "living-space": {"value", "unit"},
    "price": {"value", "currency"},
}

# starting process
pending_data = XMLToGSpread(xml_source_url, ss_table_name, keywords_parse, worksheet_name)
pending_data.send_to_spreads()

# Advanced example of parsing parameters
keywords_parse = {
    "JKSchema": [ # example of parsing multiple entries in one object
        {
            "content": {"Name", "Id"}
        },
        {
            "content": {"House>Id"}  # example of parsing nested entries with using > symbol. It goes inside "content" object, then inside "House" object and gets "Id" value
        }
    ],
    "Phones": {
        "content": {"PhoneSchema>CountryCode", "PhoneSchema>Number"},
        "merge": {"name": "Phone", "items": ["CountryCode", "Number"]} # example of parsing multiple entries in one object with using array in listing all entires names
    },
    "ExternalId": True,
    "FloorNumber": True,
    "FlatRoomsCount": True,
    "TotalArea": True,
    "LivingArea": True,
    "BargainTerms": "Price",
}
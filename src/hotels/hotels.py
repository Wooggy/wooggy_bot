import requests
from datetime import datetime, timedelta
from key_unpacker import get_from_env

headers = {
    'x-rapidapi-key': get_from_env('x-rapidapi-key'),
    'x-rapidapi-host': "hotels4.p.rapidapi.com"
}


def select_city(city: str) -> dict:
    """City parsing"""

    city_url = "https://hotels4.p.rapidapi.com/locations/search"
    city_querystring = {"query": city, "locale": "en_US"}
    city_response = requests.request("GET", city_url, headers=headers, params=city_querystring).json()

    neighborhoods = {}

    try:
        for item in city_response.get("suggestions"):
            if item.get("group") == "CITY_GROUP":
                for neighborhood in item.get("entities"):
                    neighborhoods.update({neighborhood["name"]: neighborhood["destinationId"]})
    except (TypeError, AttributeError):
        neighborhoods = {}

    return neighborhoods


def result(data: dict) -> list:
    """Parsing of results with hotels"""

    check_in = datetime.today().date()
    check_out = check_in + timedelta(days=data["days"])
    check_in = str(check_in)
    check_out = str(check_out)

    hotels_url = "https://hotels4.p.rapidapi.com/properties/list"
    hotels_querystring = {"adults1": "1", "pageNumber": "1", "destinationId": "1731364",
                          "pageSize": "25",
                          "checkOut": check_out, "checkIn": check_in, "sortOrder": "PRICE", "locale": "en_US",
                          "currency": "USD"}

    hotels = []

    try:
        for key, value in data.items():
            if key == 'days':
                continue
            hotels_querystring[key] = value

        hotels_response = requests.request("GET", hotels_url, headers=headers, params=hotels_querystring).json()

        if hotels_response.get("data").get("body").get("searchResults").get("totalCount") > 0:
            for item in hotels_response.get("data").get("body").get("searchResults").get("results"):
                hotel = item.get("name")
                stars = None if item.get("starRating") is None else round(item.get("starRating")) * "⭐"
                address = item.get("address").get("streetAddress")
                distance = item.get("landmarks")[0].get("distance")
                price = f'{item.get("ratePlan").get("price").get("current")} ' \
                        f'{item.get("ratePlan").get("price").get("info", "")}'

                hotel_info = f'Hotel: {hotel}\nClass: {stars}\nAddress: {address}\nFrom the center: {distance}' \
                             f'\nPrice: {price}'
                hotel_location = {'lat': item["coordinate"]["lat"], 'lon': item["coordinate"]["lon"]}
                hotels.append({'info': hotel_info, 'location': hotel_location})
    except (TypeError, AttributeError):
        hotels = []

    return hotels

from tqdm import tqdm
from bs4 import BeautifulSoup
import plotly.graph_objs as go
import requests
import time


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
google_places_key = 'AIzaSyDRdVbarhxIjVgyzBac6Nsw1QJmD_cQm_k'
sleep_time = 0


sites_cache = 'sites.cache'
location_cache = 'location.cache'
nearby_cache = 'nearby.cache'

cache_file = './spider.cache'
cache = {nearby_cache: {}, location_cache: {}, sites_cache: {}}


class NationalSite:
    def __init__(self, type_, name, desc, url=None):
        self.type = type_
        self.name = name
        self.description = desc
        self.url = url

        # needs to be changed, obvi.
        self.address_street = '123 Main St.'
        self.address_city = 'Smallville'
        self.address_state = 'KS'
        self.address_zip = '11111'

    def __str__(self):
        return f"{self.name} ({self.type}): {self.address_street}, {self.address_city}, " \
               f"{self.address_state} {self.address_zip}"


class NearbyPlace:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


def get_sites_for_state(state_abbr: str):
    # make it work for uppercase
    state = state_abbr.lower()

    # target url
    url = f"https://www.nps.gov/state/{state}/index.htm"
    res = requests.get(url=url, headers=headers)

    soup = BeautifulSoup(res.text, 'lxml')
    ulTag = soup.find('ul', **{'id': 'list_parks'})
    liList = ulTag.find_all('li', class_='clearfix')

    parkList = []
    for liItem in liList:
        park_type = liItem.find('h2').text
        park_name_Tag = liItem.find('h3')
        park_name = park_name_Tag.text
        park_url = "https://www.nps.gov" + park_name_Tag.find('a').get('href')
        park_desc = liItem.find('p').text

        park_street, park_city, park_state, park_zip_code = get_national_site_address(park_url)
        if not park_street:
            continue

        national_site = NationalSite(park_type, park_name, park_desc, park_url)
        national_site.address_street = park_street.strip()
        national_site.address_city = park_city.strip()
        national_site.address_state = park_state.strip()
        national_site.address_zip = park_zip_code.strip()

        parkList.append(national_site)

    # add cache
    cache[sites_cache][state] = parkList
    return parkList


def get_national_site_address(site_url):
    res = requests.get(site_url, headers=headers)
    html = res.text

    try:
        soup = BeautifulSoup(html, 'lxml')
        adr = soup.find('p', class_='adr')
        street = adr.find('span', **{'itemprop': 'streetAddress'}).text.replace('\n', '')
        city = adr.find('span', **{'itemprop': 'addressLocality'}).text
        state = adr.find('span', **{'itemprop': 'addressRegion'}).text
        zip_code = adr.find('span', **{'itemprop': 'postalCode'}).text
        return street, city, state, zip_code
    except:
        return None, None, None, None


def get_site_location(national_site: NationalSite):
    geo_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    geo_params = {
        'key': google_places_key,
        'inputtype': 'textquery',
        'input': national_site.name,
        'fields': 'geometry'
    }
    while True:
        time.sleep(sleep_time)
        geo_res = requests.get(url=geo_url, params=geo_params)
        geo_data = geo_res.json()
        if geo_data['status'] == 'ZERO_RESULTS':
            return None
        if len(geo_data.get('candidates')) != 0:
            geometry = geo_data.get('candidates')[0]['geometry']['location']
            cache[location_cache][national_site.name] = geometry
            return geometry


def get_nearby_places_for_site(national_site: NationalSite):
    geometry = get_site_location(national_site)

    near_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    near_params = {
        'location': f"{geometry.get('lat')},{geometry.get('lng')}",
        'radius': '10000',
        'key': google_places_key,
    }
    while True:
        time.sleep(sleep_time)
        near_res = requests.get(url=near_url, params=near_params)
        near_places = []
        for item in near_res.json().get('results'):
            try:
                near_places.append(NearbyPlace(item['name']))
                cache[location_cache][item['name']] = item['geometry']['location']
            except Exception as exc:
                print(repr(exc))
        if len(near_places) == 0:
            continue
        print(f"Nearby Number: {len(near_places)}")
        cache[nearby_cache][national_site.name] = near_places
        return near_places


def plot_sites_for_state(state_abbr):
    state = state_abbr.lower()
    if state in cache[sites_cache].keys():
        sites = cache[sites_cache][state]
    else:
        sites = get_sites_for_state(state)

    lat = []
    lng = []
    text = []

    for site in tqdm(sites):
        if site.name in cache[location_cache].keys():
            location = cache[location_cache][site.name]
        else:
            location = get_site_location(site)
            if not location:
                continue
            time.sleep(sleep_time)

        lat.append(location.get('lat'))
        lng.append(location.get('lng'))
        text.append(site.name)

    fig = go.Figure(
        data=go.Scattergeo(lon=lng, lat=lat, text=text, mode='markers', hoverinfo="all")
    )

    title = f'Sites for "{state_abbr}"'
    fig.update_layout(
        title=title,
        geo=dict(
            lonaxis=dict(range=[min(lng), max(lng)]),
            lataxis=dict(range=[min(lat), max(lat)])
        ),
    )
    fig.write_html(f"{state_abbr}_sites.html")


def plot_nearby_for_site(site_object: NationalSite):
    if site_object.name in cache[nearby_cache].keys():
        nearbyList = cache[nearby_cache][site_object.name]
    else:
        nearbyList = get_nearby_places_for_site(national_site=site_object)

    lat = []
    lng = []
    text = []

    for site in tqdm(nearbyList):
        if site.name in cache[location_cache].keys():
            location = cache[location_cache][site.name]
        else:
            location = get_site_location(site)
            time.sleep(sleep_time)

        lat.append(location.get('lat'))
        lng.append(location.get('lng'))
        text.append(site.name)

    fig = go.Figure(
        data=go.Scattergeo(lon=lng, lat=lat, text=text, mode='markers', hoverinfo="all")
    )

    title = f'Nearby Site for {site_object.name}'
    fig.update_layout(
        title=title,
        geo=dict(
            lonaxis=dict(range=[min(lng), max(lng)]),
            lataxis=dict(range=[min(lat), max(lat)])
        ),
    )
    fig.write_html(f"{site_object.name}_nearby.html")


def get_menu():
    res = requests.get('https://www.nps.gov/index.htm', headers=headers)
    soup = BeautifulSoup(res.text, 'lxml')
    ulTag = soup.find('ul', **{'role': 'menu'})

    state_abbr_map = {}
    for liItem in ulTag.find_all('li'):
        abbr = liItem.find('a').get('href').split("/")[2]
        state_abbr_map[abbr] = liItem.text
    return state_abbr_map


if __name__ == '__main__':
    state_abbr_dict = get_menu()
    site_sym = 'site'
    nearby_sym = 'nearby'

    help = """
list <stateabbr>
    available anytime
    lists all Nation Sites in a state
    valid inputs: a two-letter state abbreviation
nearby <result_number>
    available only if there is an active result set
    lists all Places nearby a given result
    valid inputs: an integer 1-len(result_set_size)
map
    available only if there is an active site or nearby result set
    displays the current results on a map
exit
    exits the program
help
    lists available commands (these instructions)

"""

    site_or_nearby = site_sym
    sites_result = None
    nearby_result = None
    state_abbr = None
    site_obj = None

    while True:
        try:
            command = input('Enter command (or "help" for options): ')
            if command == 'help':
                print(help)
            elif command == 'exit':
                print('Bye!')
                break
            elif command[:4] == 'list':
                _, state_abbr = command.split()
                print(f"National Sites in {state_abbr_dict[state_abbr]}\n")

                sites_result = get_sites_for_state(state_abbr)
                site_or_nearby = site_sym
                for index, item in enumerate(sites_result):
                    print(f"{index+1} {item}")
                print('\n')
            elif command[:6] == 'nearby':
                _, site_no = command.split()
                site_obj = sites_result[int(site_no) - 1]
                print(f"Places near {site_obj.name} {site_obj.type}")

                nearby_result = get_nearby_places_for_site(site_obj)
                site_or_nearby = nearby_sym
                for index, item in enumerate(nearby_result):
                    print(f"{index+1} {item.name}")
                print('\n')
            elif command == 'map':
                if site_or_nearby == site_sym:
                    plot_sites_for_state(state_abbr)
                else:
                    plot_nearby_for_site(site_obj)
            else:
                print('Bad Input!')
                print(help)
        except:
            print('Bad Inputs.')
            print(help)

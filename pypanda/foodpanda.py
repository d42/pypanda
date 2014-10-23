import sys
import json
import argparse
import math
import sqlite3

from collections import namedtuple, OrderedDict
import requests

from .oauth import OAuth
from .exceptions import (NoLocationException, TokensNotSetException,
                         BadRequestTypeException)

Restaurant = namedtuple('Restaurant', ['name', 'rating', 'review_number',
                                       'lat', 'long', 'location', 'provider'])

def api(url, params=(), method='GET', lang=True, api_key=True, oauth=True):
    def inner(func):
        def innerer(self, *args, country=None, **kwargs):
            request_parameters = {k: v for k,v in zip(params, args)}
            unassigned_params = params[len(request_parameters):]
            for p in unassigned_params:
                default = None
                if isinstance(p, tuple):
                    p, default = p

                if p in kwargs:
                    request_parameters[p] = kwargs[p]
                    continue

                state_param = getattr(self, p, None)
                if state_param is not None:
                    request_parameters[p] = state_param
                    continue

                if default:
                    request_parameters[p] = default
                    continue

            print(request_parameters)
            if country:
                api_url = self.countries[country]
            else:
                api_url = self.api_url
            endpoint = '/'.join([api_url, url])

            print(args, kwargs)
            content = self.request(endpoint, request_parameters,
                                   method=method, api_key=api_key,
                                   lang=lang, oauth=oauth,
                                   country=country).text

            return func(self, content)
        return innerer
    return inner


class FoodpandaPlugin:
    _countries = None
    _cities = None
    url_countries = "http://api.foodpanda.com/configuration/getmobilecountries"
    api_key = "EA6986E35541C59CE516692E83761"
    city_id = 0
    lang_id = 1

    def __init__(self, country=None):
        self.oauth = OAuth()

        user_agent = ("Dalvik/1.6.0 (Linux; U; Android 4.1.1;"
                      "Samsung Galaxy S2 - 4.1.1 - API 16 - 480x800"
                      "Build/JRO03S")

        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

        if country:
            self.set_country(country)

    def set_country(self, country):
        """:param str country: derpdepr"""
        country = country.capitalize()

        if country not in self.countries:
            raise NoLocationException()

        self.api_url = self.countries[country]
        self.oauth.set_token(*self.req_token())

    def set_city(self, city_name=None, city_id=None):
        if city_id:
            self.city_id = city_id
            return

        if city_name:
            city_name = city_name.capitalize()
            city_id = self.cities.get(city_name, None)
            if city_id is None:
                raise NoLocationException()
            self.city_id = city_id
        pass

    @property
    def countries(self):
        if not self._countries:
            self._countries = self.req_countries()
        return self._countries

    @property
    def cities(self):
        if not self._cities:
            self._cities = self.update_cities()
        return self._cities

    def request(self, url, params=None, method='POST',
                api_key=False, lang=False, oauth=True, country=None):

        if oauth and not self.oauth.setup:
            token, secret = self.req_token(country=country)
            self.oauth.set_token(token, secret)

        method_function = {'POST': self.session.post,
                           'GET': self.session.get}.get(method, None)
        if not method:
            raise BadRequestTypeException()

        params = params or {}
        if lang:
            params.update({'language_id': self.lang_id})
        if api_key:
            params.update({'api_key': self.api_key})

        params = OrderedDict((k, str(v)) for k, v in sorted(params.items()))
        print(method)
        oauth_data = self.oauth.oauth_data(url, params, method)
        oauth_string = ','.join('{}="{}"'.format(k, v)
                                for k, v in sorted(oauth_data.items()))

        self.session.headers['Authorization'] = 'OAuth ' + oauth_string

        req = method_function(url, params=params)
        if req.status_code != 200:
            import ipdb; ipdb.set_trace()

        return req

    def req_countries(self):
        """ request available countries and their respective api urls """
        params = {
            'environment': 'live',
            'platform': 'android',
            'version': '3.0',
            'brand': 'foodpanda'
        }
        content = self.request(self.url_countries, params, 'GET', oauth=False).text
        return {e['title']: e['url'] for e in json.loads(content)['data']}

    @api('addresses/geocoding', ['name', 'city_id', ('extended', True)],
         method='GET', api_key=True, lang=True)
    def req_geocoding(self, content):
        """ request street names (and coordinates if extended)
            that start with :param name: """

        return json.loads(content)['data']['items']

    @api('vendors', ['latitude', 'longitude'])
    def req_vendors(self, content):
        """request vendors near this latitude, longitude"""
        for e in json.loads(content)['data']['items']:
            yield Restaurant(e['name'], e['rating'], e['review_number'],
                             e['latitude'], e['longitude'], e['address'],
                             self)

    def req_nearest_vendors(self, latitude, longitude):
        def dist(element):
            e_lat = element.lat
            e_lon = element.long
            if not e_lat or not e_lon:
                return float('inf')

            return sum([(float(latitude) - float(e_lat))**2,
                       (float(longitude) - float(e_lon))**2])

        return sorted(self.req_vendors(latitude, longitude), key=dist)

    @api('oauth/request_token', method='POST', oauth=False,
         lang=False, api_key=False)
    def req_token(self, content):
        data = json.loads(content)['data']
        secret = data['o_auth_token_secret']
        token = data['o_auth_token']
        return secret, token

    @api('configuration')
    def req_configuration(self, content):
        return(content)

    @api('cities')
    def req_cities(self, content):
        cities = {e['name']: e['id'] for e in json.loads(content)['data']['items']}
        return cities

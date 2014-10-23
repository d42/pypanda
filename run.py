import argparse
import sys

from pypanda.foodpanda import FoodpandaPlugin

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("country", default="Poland")
    #parser.add_argument("city", default=1)
    parser.add_argument("--lat", default=1)
    parser.add_argument("--long", default=1)
    options = parser.parse_args(sys.argv[1:])

    country = options.country
    #city = options.city
    f = FoodpandaPlugin()

    #if options.lat and options.long:
        #for e in f.closest(options.lat, options.long):
            #print(e)

    #f.set_city(city)
    print(f.req_geocoding("Plac Bankowy", city_id=1, country="Poland"))
    import ipdb; ipdb.set_trace()

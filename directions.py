from errbot.botplugin import BotPlugin
from errbot.jabberbot import botcmd
from urllib import quote
import simplejson
from urllib2 import urlopen

__author__ = 'atalyad'

DIRECTIONS_URL = 'http://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&sensor=false'

class Directions(BotPlugin):

    min_err_version = '1.2.1' # make err split the arguments for you

    def generate_directions_str(self, json_res):

        ans = ''
        if 'routes' in json_res and len(json_res['routes']):
            for route in json_res['routes']:
                ans += 'Route: '
                for leg in route['legs']:
                    ans += 'From %s\n' % leg['start_address']
                    ans += 'To %s\n' % leg['end_address']
                    ans += '%s\n' % leg['duration']['text']

                    for step in leg['steps']:
                        ans += step['html_instructions'].replace('/<[^>]+>/g', ' ')
                        ans += ' (%s)\n' % step['distance']['text']

                if 'warnings' in route and route['warnings']:
                    ans += 'Warnings: ' + ','.join(route['warnings'])

                ans += '\n\n'
        return ans.strip('\n')


    @botcmd(split_args_with=':')
    def directions(self, mess, args):
        """
        Returns the directions from origin to destination using Google directions api.
        !directions origin:destination:mode
        *mode is not required, defaults to driving.
        """
        if len(args) < 2:
            return 'Please supply an origin and a destination separated by a ":". Travel mode is optional (defaults to driving. Options are: "driving", "walking", "bicycling", "transit").'

        url = DIRECTIONS_URL % (quote(args[0].encode('utf-8')), quote(args[1].encode('utf-8')))
        if len(args) == 3:
            url += '&mode=%s' % args[2].strip()

        content = urlopen(url)
        results = simplejson.load(content)

        if results['status'] != 'OK':
            return results['status']

        return self.generate_directions_str(results)
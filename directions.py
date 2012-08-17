import logging
import re

# Backward compatibility
from errbot.version import VERSION
from errbot.utils import version2array
if version2array(VERSION) >= [1,6,0]:
    from errbot import botcmd, BotPlugin
else:
    from errbot.botplugin import BotPlugin
    from errbot.jabberbot import botcmd

from urllib import quote
import simplejson
from urllib2 import urlopen

__author__ = 'atalyad'

DIRECTIONS_URL = 'http://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&sensor=false&mode=%s'


def generate(mode):
    f = lambda self, mess, args: self.bare_directions(args, mode)
    f.__name__ = 'directions_%s' % mode
    f.__doc__ = "Returns the %s directions from origin to destination using Google directions api.\n!directions_%s origin -> destination" % (mode, mode)
    return botcmd(f, split_args_with='->')


class DirectionsBuilder(type):
    MODES = ('driving', 'walking', 'bicycling', 'transit')
    def __new__(mcs, name, bases, classDict):
        newClassDict = dict(classDict.items() +
                            [('directions_%s' % mode, botcmd(generate(mode)))
                            for mode in mcs.MODES])
        return super(DirectionsBuilder, mcs).__new__(mcs, name, bases, newClassDict)


class Directions(BotPlugin):
    __metaclass__ = DirectionsBuilder

    min_err_version = '1.4.1' # need a bug correction on the metaclasses generation

    def generate_directions_str(self, json_res):
        remove_html_tags = re.compile(r'<.*?>')
        too_many_spaces = re.compile(r'  +')

        ans = ''
        if 'routes' in json_res and len(json_res['routes']):
            for route in json_res['routes']:
                ans += 'Route: '
                for leg in route['legs']:
                    ans += 'From %s\n' % leg['start_address']
                    ans += 'To %s\n' % leg['end_address']
                    ans += '%s\n' % leg['duration']['text']

                    for step in leg['steps']:
                        ans += too_many_spaces.sub(' ', remove_html_tags.sub(' ', step['html_instructions']))
                        ans += ' (%s)\n' % step['distance']['text']

                if 'warnings' in route and route['warnings']:
                    ans += 'Warnings: ' + ','.join(route['warnings'])

                ans += '\n\n'
        return ans.strip('\n')

    def get_directions(self, A, B, mode):
        logging.debug('Directions from %s to %s by %s' % (A, B, mode))
        url = DIRECTIONS_URL % (quote(A.encode('utf-8')), quote(B.encode('utf-8')), mode)

        content = urlopen(url)
        results = simplejson.load(content)

        if results['status'] != 'OK':
            return results['status']

        return self.generate_directions_str(results)

    def bare_directions(self, args, mode='driving'):
        if len(args) < 2:
            return 'Please supply an origin and a destination separated by a "->". like : Paris, France -> Marseille, France '
        return self.get_directions(args[0], args[1], mode)


    @botcmd(split_args_with='->')
    def directions(self, mess, args):
        """
        Returns the driving directions from origin to destination using Google directions api.
        !directions origin -> destination
        """
        return self.bare_directions(args)




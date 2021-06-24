"""Petoi automate running

Connect to petoi via serial agent. 
Petoi then performs a randomly selected motion at random intervals.

Usage:
    1. Create action set in /{install directory}/resources/automate.json 
    2. Move to the 'src' directory.
    3. Run '{your python interpreter} ./bin/automate.py'
"""
import sys
import os
import traceback
import time
from configparser import ConfigParser, ExtendedInterpolation
import logging
import json
from random import choice, randrange

sys.path.insert(0, os.path.abspath('.'))

from modules.serial_agent import CommandPack, make_serial_agent, terminate_serial_agent


CONF_FILE = 'settings.cfg'

ACT_TIMES_DEFAULT = 3
ACT_INTERVAL_RANGE_MIN = 3
ACT_INTERVAL_RANGE_MAX = 5

def init_logger(log_conf):
    logging.basicConfig(
        format=log_conf['format'],
        datefmt=log_conf['datefmt'],
        level=log_conf['loglevel_automate']
    )


if __name__ == '__main__':
    conf = ConfigParser(interpolation=ExtendedInterpolation())
    conf.read(CONF_FILE)

    init_logger(conf['Logging'])

    # Connect petoi
    try:
        agent = make_serial_agent(conf.get('Petoi', 'port', fallback=None))
    except:
        sys.exit(traceback.format_exc())
    else:
        if agent is None:
            sys.exit('Board is not ready. Please try again!')

    # Load action scenario
    action_scenario = f"{conf.get('Path', 'resources')}/automate.json"
    try:
        with open(action_scenario, 'r') as fp:
            commands = json.load(fp)
    except FileNotFoundError as e:
        sys.exit(f"Not found action scenario ({action_scenario})")

    # Start action
    act_cnt = 0
    while True:
        act_cnt += 1
        picked = choice(commands)
        command_pack = CommandPack(picked['commands'])

        logging.info("Act take %d [%s]", act_cnt, picked['name'])
        for action in command_pack.items:
            agent.write_command(action['cmd'], action['duration'])

        agent.read_port()
        # print('\n'+'\n'.join(agent.read_port()))

        if act_cnt >= conf.getint('Automate', 'act_times', fallback=ACT_TIMES_DEFAULT):
            logging.info("Bye!")
            break

        interval_range_min = conf.getint('Automate', 'act_interval_min', fallback=ACT_INTERVAL_RANGE_MIN)
        interval_range_max = conf.getint('Automate', 'act_interval_max', fallback=ACT_INTERVAL_RANGE_MAX)
        try:
            idlesleep = randrange(interval_range_min, interval_range_max, 1)
        except ValueError:
            logging.error(
                "False to get randam value for the idle sleep (range: %d to %d)", 
                interval_range_min, interval_range_max)
            idlesleep = ACT_INTERVAL_RANGE_MAX

        logging.info("Idle sleep %dmin", idlesleep)
        time.sleep(idlesleep*60)

    terminate_serial_agent(agent)
    sys.exit()

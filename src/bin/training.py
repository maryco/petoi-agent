"""Utility module for creating petoi's original actions.

Send multiple commands to the Petoi as a performance scenario.

Usage:
    1. Move to the 'src' directory.
    2. Run '{your python interpreter} ./bin/training.py'
"""
import sys
import os
import traceback
from configparser import ConfigParser, ExtendedInterpolation
import logging
import re

sys.path.insert(0, os.path.abspath('.'))

from modules.serial_agent import CommandPack, make_serial_agent, terminate_serial_agent


CONF_FILE = 'settings.cfg'

INPUT_SESSION_MAX = 100

def init_logger(log_conf):
    logging.basicConfig(
        format=log_conf['format'],
        datefmt=log_conf['datefmt'],
        level=log_conf['loglevel_training']
    )


def print_usage():
    print('----------------------------')
    print('Ex) Sit 3sec, wait a 2sec.')
    print('>>> ksit,3')
    print('>>> sleep,2')
    print('>>> run')
    print('----------------------------')
    print('---Available commands---')
    print('[dry-run] Show the queued command list.')
    print('[run] Sends all queued command to the petoi and clear them.')
    print('[clear] Clear all queued commands.')
    print('[exit] Quit the training.')
    print('[quit] Quit the training.')
    print('----------------------------')


if __name__ == '__main__':
    conf = ConfigParser(interpolation=ExtendedInterpolation())
    conf.read(CONF_FILE)

    init_logger(conf['Logging'])

    # Connect petoi
    try:
        print('...Please wait for a while until connect to the petoi.')
        agent = make_serial_agent(conf.get('Petoi', 'port', fallback=None))
    except:
        sys.exit(traceback.format_exc())
    else:
        if agent is None:
            sys.exit('Board is not ready. Please try again!')

    # Start the training operation.
    input_cnt = 0
    cmd_pack = CommandPack()
    print_usage()

    while True:
        input_cnt += 1
        if input_cnt > INPUT_SESSION_MAX:
            break

        buff = input('BOW-WOW?>>> ').strip()
        if len(buff) == 0:
            continue

        if buff == 'quit' or buff == 'exit':
            print('Bye!')
            break

        if buff == 'clear':
            cmd_pack.clear_items()
            print('Cleared all commands.')
            continue

        if buff == 'dry-run':
            print('Currently, the command is:')
            print(repr(cmd_pack))
            continue

        if buff == 'run':
            if len(cmd_pack.items) == 0:
                print('There is no command.')
                continue

            for action in cmd_pack.items:
                agent.write_command(action['cmd'], action['duration'])

            if agent.has_error_response():
                print('Something wrongs in the commands.')

            cmd_pack.clear_items()

        if re.match(r'^[^,]+,{1}[0-9]+$', buff) is not None:
            cmd, duration = buff.split(',')
            if cmd.strip() == 'sleep':
                cmd = ''

            if cmd_pack.set_item(cmd.strip(), duration.strip()):
                print(f"Added command as cmd:{cmd} duration:{duration}sec")
            else:
                print(f"Failed to add a command, see the validation rules below.")
                print(f"- The 'command' must be a string.")
                print(f"- The 'duration' should be in the range 0 to {CommandPack.MAX_DURATION} of integer.")
                print(f"- The 'command' and 'duration' must be separated by commas.")

    terminate_serial_agent(agent)
    sys.exit()

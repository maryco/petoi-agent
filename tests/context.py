"""The context module for run the test

Notes:
    - Run the test in the parent directory of "src".

Example: Run all tests in the specified file.
    % pipenv run python -m unittest -v tests.test_serial_agent
    % pipenv run python -m unittest -v tests.test_serial_agent.TestSerialAgent

Example: Run specified test case.
    % pipenv run python -m unittest -v tests.test_serial_agent.TestSerialAgent.test_create_incetanse
"""

import sys
import os
from datetime import date
import logging
import subprocess
import re

sys.path.insert(0, os.path.abspath('./src'))

TESTING_LOG_LEVEL = logging.DEBUG

def init_test_logger():
    filepath = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig(
        filename=f'{filepath}/logs/{(date.today()).strftime("%Y%m%d")}.log',
        format='%(asctime)s-[%(name)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=TESTING_LOG_LEVEL
    )

def has_active_devenv():
    cp = subprocess.run(['which', 'docker'])
    if cp.returncode != 0:
        return False

    cp = subprocess.run(['docker', 'ps'], stdout=subprocess.PIPE)
    if cp.returncode != 0:
        return False

    active_container_cnt = 0
    for line in cp.stdout.decode('utf-8').split('\n'):
        if re.search('app\-django|app\-node', line) is not None:
            active_container_cnt += 1

    return active_container_cnt == 2
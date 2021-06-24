import traceback
import time
import logging
import re
import json
import serial


class SerialAgent:
    """Agent class for communicating with 'Petoi' via serial port."""

    # Baud rate
    BAUNDRATE = 115200

    # The seconds of waiting for the board initialized
    # when connect the serial port.
    START_UP_WAITING: int = 10

    # The max number of loop count for receive buffer reads,
    # to prevent port blocking.
    # https://pyserial.readthedocs.io/en/latest/shortintro.html#readline
    MAX_READABLE_LINE = 500

    # Delay to down the reading receive buffer read speed.
    REPEAT_READ_DELAY: float = 0.01

    # The min seconds of sleep time after sending a command.
    MIN_ACT_DURATION: int = 5

    # **Below messages are from the 'Bittle' on 'NyBoard_V1_0'**
    BOARD_INIT_MESSAGES = (
        # * Start *
        # Initialize I2C
        # Connect MPU6050
        # Test connection
        # MPU successful
        # Initialize DMP
        # 1283 105 26 61
        # Enable DMP
        # Enable interrupt
        'DMP ready!',
    )

    BOARD_ERROR_MESSAGES = (
        'wrong key!',
    )

    def __init__(self, port, serial_api=None, **kwargs) -> None:
        """Set or create serial api instance.

        Args:
            port (str): name of the target port 
            serial_api (Any, optional): Instance of serial api class. Defaults to PySerial.

        See also:
            https://pyserial.readthedocs.io/en/latest/index.html
        """

        self.min_act_duration = kwargs.get(
            'min_act_duration', self.MIN_ACT_DURATION)

        self.is_board_ready = False

        if serial_api is None:
            self._ser = serial.Serial(
                port=port,
                baudrate=self.BAUNDRATE,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=1
            )
        else:
            self._ser = serial_api

        time.sleep(self.START_UP_WAITING)

        if (not self._ser.is_open):
            logging.warning('Port [%s] is not opened.', port)

    def open_port(self, attempt=1, retry_interval=5):
        """If the board is not ready, it will try to open and close the serial port.

        Args:
            attempt (int, optional): Number of trials. Defaults to 1.
            retry_interval (int, optional): Seconds for retry interval. Defaults to 5.

        Returns:
            bool:
        """
        if self.is_ready():
            return True

        attempt_count = 0
        while True:
            attempt_count += 1
            try:
                logging.debug(
                    'Try reopen port [%d/%d]', attempt_count, attempt)
                self.close_port()
                self._ser.open()

                if attempt == 1:
                    time.sleep(self.START_UP_WAITING)
                else:
                    time.sleep(retry_interval)
            except:
                logging.error('Fails to open port (%s)',
                              traceback.format_exc())
                raise

            if self.is_ready():
                break

            if attempt_count >= attempt:
                break

        return self._ser.is_open

    def close_port(self):
        """Close the serial port"""

        if (not self._ser.is_open):
            logging.debug('Port is already closed.')
            return True

        self._ser.close()
        return self._ser.is_open

    def write_command(self, cmd: str, duration: int):
        """Send a command and sleep specified duration

        Args:
            cmd (str): String of **correct** command (if empty is just sleep)
            duration (int): Seconds of sleep time after sending a command

        Returns:
            bool:

        Notes:
            - See below for examples of correct commands for the 'Bittle'.
              https://bittle.petoi.com/4-configuration#4-3-arduino-ide-as-an-interface

            - If the duration is less then the minimum duration(default is 5sec), 
              it will be set to the default.
        """
        if not self._ser.is_open:
            self._ser.open()
            time.sleep(self.START_UP_WAITING)

        write_len = 0
        if (cmd != '' and duration < self.min_act_duration):
            duration = self.min_act_duration

        logging.debug('Act cmd[%s], duration[%d]', cmd, duration)
        if cmd != '':
            try:
                write_len = self._ser.write(str(cmd).encode('utf-8'))
            except:
                logging.error(
                    'Fails to write command cmd[%s] duration[%d] (%s)', cmd, duration, traceback.format_exc())
                raise
            else:
                self._ser.flush()

        time.sleep(duration)
        return not cmd or write_len > 0

    def read_port(self):
        """Returns all in the receive buffer as a string list"""

        if (not self._ser.is_open or self._ser.in_waiting == 0):
            logging.debug(
                'Nothing in input buffer (port is open ? [%s])',
                self._ser.is_open)
            return []

        msg = []
        repeat_counter = 0
        while True:
            time.sleep(self.REPEAT_READ_DELAY)
            repeat_counter += 1
            if (self._ser.in_waiting == 0 or repeat_counter > self.MAX_READABLE_LINE):
                break

            buff = self._ser.readline()
            if type(buff) == bytes:
                msg.append(re.sub(
                    '\n|\r\n', '', buff.decode('utf-8', 'ignore')))
                # logging.debug('<<< %s', re.sub(
                #    '\n|\r\n', '', buff.decode('utf-8', 'ignore')))

        return msg

    def is_ready(self):
        """Checks the serial port is open and board is initialized.
        
            **For the 'Bittle' on 'NyBoard_V1_0'**
        """
        if not self._ser.is_open:
            return False

        if self.is_board_ready:
            return True

        messages = self.read_port()
        self.is_board_ready = any(msg for msg in messages if msg in self.BOARD_INIT_MESSAGES)
        return self.is_board_ready

    def has_error_response(self):
        """Return 'True' if the board buffer contains error msg."""
        messages = self.read_port()
        if len(messages) == 0:
            return False
        
        return any(msg for msg in messages if msg in self.BOARD_ERROR_MESSAGES)

    def __repr__(self) -> str:
        # default type is <class 'src.serial_agent.SerialAgent'>
        return 'SerialAgent'


class CommandPack():
    """Model class for the 'Petoi' command."""

    MAX_DURATION = 300

    def __init__(self, data=None) -> None:
        self.items = []

        if data is None:
            return

        if type(data) is list:
            self._set_items(data)
            return

        try:
            tmp = json.loads(data)
        except:
            logging.error('Fails to load json. (%s)', traceback.format_exc())
            raise
        else:
            self._set_items(tmp.get('commandPack', []))

    def set_item(self, cmd, duration):
        """Validate parameter and append to the list."""
        if not self.is_valid_cmd(cmd):
            return False
        if not self.is_valid_duration(duration):
            return False

        self.items.append({'cmd': cmd, 'duration': int(duration)})
        return True

    def is_valid_cmd(self, cmd):
        """Validate command string

            **It's not checking if the command is correct, just check the type of the value.**
            **Therefore, be careful not to break your 'Petoi' with the wrong command.**
        """
        if type(cmd) is not str:
            return False

        return True

    def is_valid_duration(self, duration):
        """Validate duration

            **The safe duration should be longer than the acting motions.**
            **Try adjusting to match the performance of your petoi.**
        Rules:
            - Type is integer.
            - Range is 0 to MAX_DURATION (Default 300)
        """
        try:
            duration = int(duration)
        except ValueError:
            logging.debug("Duration must be an integer value (%r).", duration)
            return False

        if duration < 0 or duration > self.MAX_DURATION:
            logging.debug("Duration should be in the range 0 to %dsec (%d).",
                          self.MAX_DURATION, duration)
            return False

        return True

    def clear_items(self):
        """Clear the command list"""
        self.items = []

    def _set_items(self, src_items):
        """Append valid command dict to the list.

        Examples:
            correct: {cmd: 'ksit', duration:5}
            correct(i.e do nothing): {cmd: '', duration:0}
        """
        if not src_items:
            return

        for item in src_items:
            if type(item) is not dict:
                logging.debug("Invalid item (%r).", item)
                continue

            duration = item.get('duration', 0)
            if not self.is_valid_duration(duration):
                continue

            cmd = item.get('cmd', '')
            if not self.is_valid_cmd(cmd):
                continue

            self.items.append({'cmd': cmd, 'duration': int(duration)})

    def __repr__(self) -> str:
        if len(self.items) == 0:
            return 'Empty'

        return '\n'.join([f"cmd:{item['cmd']}, duration:{item['duration']}" for item in self.items])


def make_serial_agent(port):
    """Create a SerialAgent instance and try to open it with the board ready"""
    agent = SerialAgent(port, min_act_duration=1)

    if not agent.is_ready():
        logging.info(
            'The board is not ready, so i try open the port again.')
        agent.open_port(attempt=3, retry_interval=10)

    if not agent.is_ready():
        return None

    return agent


def terminate_serial_agent(agent, act_down=True):
    """Send a command of 'down' and close the port"""
    if act_down:
        agent.write_command('d', 3)

    agent.read_port()
    agent.close_port()


if __name__ == '__main__':
    pass

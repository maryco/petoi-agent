from datetime import date
import unittest
from unittest import mock
from unittest.case import SkipTest
from unittest.mock import Mock, MagicMock, call, patch
import serial

from tests.context import *
from modules.serial_agent import SerialAgent

class TestSerialAgent(unittest.TestCase):

    TEST_SERIAL_PORT = '/dev/tty.Dummy-Port'

    @classmethod
    def setUpClass(cls) -> None:
        init_test_logger()
        return super().setUpClass()

    def setUp(self) -> None:
        self.time_sleep_patcher = patch('time.sleep')
        self.time_sleep_mock = self.time_sleep_patcher.start()
        return super().setUp()

    def tearDown(self) -> None:
        self.time_sleep_patcher.stop()
        return super().tearDown()

    def addCleanup(self, function, *args, **kwargs) -> None:
        patch.stopall()
        return super().addCleanup(function, *args, **kwargs)

    @SkipTest
    def test_create_incetanse_with_loopback(self):
        """Testing with loopback connection but not working so under skipped!

        Note:
            https://pythonhosted.org/pyserial/url_handlers.html#loop
        """
        agent = SerialAgent(port='loop://')
        self.assertIsInstance(agent, SerialAgent)

    @patch('serial.Serial')
    def test_create_incetanse(self, serial_mock):
        # Note: If set 'serial_api=mockSerialObj' __init__ is not colled?
        agent = SerialAgent(port=self.TEST_SERIAL_PORT)
        self.assertIsInstance(agent, SerialAgent)

        # pySerial initialized with expected.
        # print(f'test_create_incetanse :{mockSerialObj.mock_calls!r}')
        expected_call = call(baudrate=115200, bytesize=8, parity='N',
                            port=self.TEST_SERIAL_PORT, stopbits=1, timeout=1)
        self.assertEqual(expected_call, serial_mock.call_args_list[0])

        # Note: kwargs is here.
        # print(mockSerialObj.call_args_list[0][1])
        # >>> {'port': '/dev/Dummy-Port', 'baudrate': 115200, 'parity': 'N', 'stopbits': 1, 'bytesize': 8, 'timeout': 1}

    @patch('serial.Serial')
    def test_close_port(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_api=serial_mock)

        agent.close_port()
        # print(mockSerialObj.mock_calls)
        serial_mock.close.assert_called()

    @patch('serial.Serial')
    def test_close_port_for_closed(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_api=serial_mock)

        with patch.object(serial_mock, 'is_open', False):
            agent.close_port()
            # print(mockSerialObj.mock_calls)
            serial_mock.close.assert_not_called()

    @patch('serial.Serial')
    def test_open_port(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_api=serial_mock)

        with patch.object(serial_mock, 'is_open', False):
            agent.open_port()
            serial_mock.open.assert_called()

    @patch('serial.Serial', **{'readline.return_value': b'DMP ready!'})
    def test_open_port_for_already_open(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_api=serial_mock)
        agent._ser = serial_mock

        with patch.object(serial_mock, 'is_open', True):
            agent.open_port()
            serial_mock.open.assert_not_called()

    @patch('serial.Serial', **{'write.return_value': 1})
    def test_write_command(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_agent=serial_mock)

        # FIXME: Why serial.Serial.write() is not mocking in SerialAgent?
        agent._ser = serial_mock

        res = agent.write_command('ksit', 10)

        self.assertTrue(res)
        serial_mock.write.assert_called_with(b'ksit')
        self.time_sleep_mock.assert_any_call(10)

    @patch('serial.Serial', **{'write.return_value': 1})
    def test_write_command_with_empty_command(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_agent=serial_mock)
        agent._ser = serial_mock

        res = agent.write_command('', 11)

        self.assertTrue(res)
        serial_mock.write.assert_not_called()
        self.time_sleep_mock.assert_any_call(11)

    @patch('serial.Serial', **{'write.return_value': 1})
    def test_write_command_with_just_sleep(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_agent=serial_mock)
        agent._ser = serial_mock

        res = agent.write_command('', 1)

        self.assertTrue(res)
        serial_mock.write.assert_not_called()
        expected_calls = [call(SerialAgent.START_UP_WAITING), call(1)]
        self.time_sleep_mock.assert_has_calls(expected_calls)
        
    @patch('serial.Serial', **{'write.return_value': 1})
    def test_write_command_with_too_short_duration(self, serial_mock):
        agent = SerialAgent(self.TEST_SERIAL_PORT, serial_agent=serial_mock)
        agent._ser = serial_mock

        res = agent.write_command('ktr', 1)

        self.assertTrue(res)
        serial_mock.write.assert_called()
        expected_calls = [call(SerialAgent.START_UP_WAITING), call(SerialAgent.MIN_ACT_DURATION)]
        self.time_sleep_mock.assert_has_calls(expected_calls)

if __name__ == '__main__':
    unittest.main()

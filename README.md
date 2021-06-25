# Serial agent for the Bittle of the Petoi.

Operate the '[Bittle](https://bittle.petoi.com/) of the Petoi' through the serial port.

## Note 

- Only for the 'Bittle' on the Arduino board version **'NyBoard_V1_0'**
  - **Be careful not to break your 'Petoi' with the wrong command.**
  - See below for examples of correct commands for the 'Bittle'.<br>
  https://bittle.petoi.com/4-configuration#4-3-arduino-ide-as-an-interface
  
- Developed with Python 3.7.10.

----

## Instllation

Install via pip or pipenv.

### Using [pip](https://pip.pypa.io/en/stable/)

```
$ pip install -r requirements.txt
```

If you want to run the tests, also install 'requests-mock'.
```
$ pip install requests-mock==1.9.2
```

### Using [pipenv](https://pipenv.kennethreitz.org/en/latest/)

```
$ pipenv install
```
If you want to run the tests, install with the option '--dev'.

## Usage

### Configuration

1. Copy the file '[settings.cfg.sample](./src/settings.cfg.sample)' to 'settings.cfg'
1. Edit the required settings.

```settings.cfg
[Path]
# Set full path to the application root directory.
app_root = /Users/you/petoi-agent/src

[Petoi]
# Set the port of your Petoi
# Note: How listing ports is https://pythonhosted.org/pyserial/shortintro.html#listing-ports
port = /dev/tty.BittleSPP-999999-Port
```

### Automate your bittle

Connect to petoi via serial agent. Petoi then performs a randomly selected motion at random intervals.

1. Create action set in /{install directory}/resources/automate.json
    - See the action samples in [automate.sample.bittle.json](./src/resources/automate.sample.bittle.json) 
1. Change to the 'src' directory.
1. Run '{your python interpreter} ./bin/automate.py'.

You can adjust automate settings in the 'settings.cfg'.
```settings.cfg
[Automate]
# Minute interval to start the action.
# Note: It's picked random between act_interval_min to act_interval_max
act_interval_min = 2
act_interval_max = 5

# The number of times to perform the action.
act_times = 5
```

### Training your bittle

Send multiple commands to the Petoi as a performance scenario.

1. Change to the 'src' directory.
1. Run '{your python interpreter} ./bin/training.py'

    Example : (Sit for 3sec and then wait for 2sec.)
    ```
    $ python ./bin/training.py
    ...Please wait for a while until connect to the petoi.
    BOW-WOW?>>> ksit,3
    Added command as cmd:ksit duration:3sec
    BOW-WOW?>>> sleep,2
    Added command as cmd: duration:2sec
    BOW-WOW?>>> run
    ```

Available commands
| Command | Description |
| --- | --- |
| dry-run | Show the queued command list. |
| run | Sends all queued command to the petoi and clear them. |
| clear | Clear all queued commands. |
| exit | Quit the training. |
| quit | Quit the training. |

---

### Execution of test code.

1. Change to the parent directory of "src".
1. Run the test.

    EX) Run all tests in the specified file.
    ```
    $ python -m unittest -v tests.test_serial_agent
    ```

    EX) Run specified test case.
    ```
    $ python -m unittest -v tests.test_serial_agent.TestSerialAgent.test_create_incetanse
    ```

--- 

## Licence

MIT


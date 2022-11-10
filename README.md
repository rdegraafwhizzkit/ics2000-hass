# ICS-2000 Home Assistant integration

This integration shows how you would integrate an ICS-2000 into Home Assistant.

### Installation
Install the Python package that includes the classes to interact with the ICS-2000 in your Home Assistant installation:
```python
pip install --upgrade git+https://github.com/rdegraafwhizzkit/ics2000-python@master#egg=ics2000
```
or, if you are (further) developing the integration, install all of them:
```python
pip install --upgrade -r dev_requirements.txt
```

Copy the custom_components/ics2000/ folder to `<config_dir>/custom_components/ics2000/`.

Add the following entry in your `<config_dir>/configuration.yaml`:

```yaml
light:                                      
  - platform: ics2000                       
    mac: MAC_HERE                
    email: EMAIL_HERE     
    password: PASSWORD_HERE_OR_secrets.yaml
    tries: 3  # Optional, defaults to 3
    sleep: 2  # Optional, defaults to 3
```
You may also add `tries` and `sleep` to the config. The ICS-2000/KAKU has no way of knowing what the
current state of a connected device is and sometimes the command does not seem to reach the device.
If you do not experience any failures, set tries to 1. Between tries, `sleep` seconds will be paused.

With default settings, the command will be sent 3 times with a 3 seconds sleep in between, 
leading to a 6 second runtime for the command: click - pause - click - pause - click.
 
Note that the actual sending of the command is done in a separate 'non-UI thread' and for that reason
a check is done (for now) that only one device is controlled at a time. This will be improved. 

Restart Home Assistant and add a 'Light' card to your dashboard using one of the 'light' entities.

## Notes on testing on macOS
When installing dependencies on macOS it may be necessary (depending on your setup)
to add some values to the environment (needs Homebrew):
```
brew install openssl@1.1
  
CPATH=/usr/local/Cellar/openssl\@1.1/1.1.1s/include/ \
  LIBRARY_PATH=/usr/local/Cellar/openssl\@1.1/1.1.1s/lib/ \
  pip install --upgrade -r dev_requirements.txt 
```
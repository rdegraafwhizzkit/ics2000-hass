# ICS-2000 Home Assistant integration

This integration shows how you can use an ICS-2000 in Home Assistant.

### Installation
* Install HACS in Home Assistant using instructions found at https://hacs.xyz/docs/setup/download/
* Add a custom _integration_ repository in HACS with url https://github.com/rdegraafwhizzkit/ics2000-hass
* Select this custom repository in HACS and click 'DOWNLOAD'
* Add the File editor add on in Home Assistant. Using File editor, add the following entry in your `<config_dir>/configuration.yaml`:

```yaml
light:                                      
  - platform: ics2000
    mac: MAC_HERE
    email: EMAIL_HERE
    password: PASSWORD_HERE_OR_secrets.yaml
    tries: 3                              # Optional, defaults to 1
    sleep: 2                              # Optional, defaults to 3
    aes: 185dd26964b583ca097231a7ea3ba407 # Optional
    ip_address: 192.168.1.205             # Optional
```
* Restart Home Assistant

You may also add `tries` and `sleep` to the config. The ICS-2000/KAKU has no way of knowing what the
current state of a connected device is and sometimes the command does not seem to reach the device.
If you do not experience any failures, set tries to 1. Between tries, `sleep` seconds will be paused.

With default settings, the command will be sent 3 times with a 3 seconds sleep in between, 
leading to a 6 second runtime for the command: click - pause - click - pause - click.
 
Note that the actual sending of the command is done in a separate 'non-UI thread' and for that reason
a check is done if a device has a thread running at that time. 

Restart Home Assistant and add a 'Light' card to your dashboard using one of the 'light' entities.

## Troubleshooting
When you receive an error the first time you'd like to add a 'Light' card, it may be helpful to
add or test with a 'Button' card for the entity first and then add a 'light' card. It
seems to trigger integration to be recognized as producing light entities.

## Notes on testing on macOS
When installing dependencies on macOS it may be necessary (depending on your setup)
to add some values to the environment (needs Homebrew):
```
brew install openssl@1.1
  
CPATH=/usr/local/Cellar/openssl\@1.1/1.1.1s/include/ \
  LIBRARY_PATH=/usr/local/Cellar/openssl\@1.1/1.1.1s/lib/ \
  pip install --upgrade -r dev_requirements.txt 
```
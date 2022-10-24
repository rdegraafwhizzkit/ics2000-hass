# ICS-2000 Home Assistant integration

This integration shows how you would integrate an ICS-2000 into Home Assistant.

### Installation
Install the Python package that includes the classes to interact with the ICS-2000:
```python
pip install --upgrade git+https://github.com/rdegraafwhizzkit/ics2000-python@master#egg=ics2000

```

Copy the custom_components/ics2000/ folder to `<config_dir>/custom_components/ics2000/`.

Add the following entry in your `<config_dir>/configuration.yaml`:

```yaml
light:                                      
  - platform: ics2000                       
    mac: MAC_HERE                
    email: EMAIL_HERE     
    password: PASSWORD_HERE_OR_secrets.yaml
```

Restart Home Assistant and add a 'Light' card to your dashboard using one of the 'light' entities.

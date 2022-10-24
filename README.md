# ICS-2000 Home Assistant integration

This integration shows how you would integrate an ICS-2000 into Home Assistant.

### Installation

Copy the custom_components/ics2000/ folder to `<config_dir>/custom_components/ics2000/`.
Add the following entry in your `configuration.yaml`:

```yaml
light:                                      
  - platform: ics2000                       
    mac: MAC_HERE                
    email: EMAIL_HERE     
    password: PASSWORD_HERE_OR_secrets.yaml
```

#!/usr/bin/python3
import requests
import json
import rofi_menu
import config

#Preferences
lightOnSymbol = "󰌵"
lightOffSymbol = "󰌶"

#Hue API
hueRoomName = config.hueRoomName
hueIP = config.hueIP
hueUsername = config.hueUsername
hueClientKey = config.hueClientKey

#Colors
#format: "name": ["icon", "hex"]
colors = [
    ["⚪ White", "#ffffff"],
    ["🪷 Pink", "#ff5487"],
    ["🔴 Red", "#ff0000"],
    ["🔵 Blue", "#0800ff"]
]


hueURL = 'https://' + hueIP + '/clip/v2/resource'

def hexToXY(hex):

    strippedHex = hex.lstrip('#')
    rgb = tuple(int(strippedHex[i:i+2], 16) for i in (0, 2, 4))
    
    red = rgb[0]
    green = rgb[1]
    blue = rgb[2]
    
    if red > 0.04045: 
        red = float((red + 0.055) / (1.0 + 0.055) ** 2.4)

    else: 
        red = float((red / 12.92));

    if green > 0.04045:
        green = float((green + 0.055) / (1.0 + 0.055) ** 2.4)
    
    else:
        green = float((green / 12.92));

    if blue > 0.04045:
        blue = float((blue + 0.055) / (1.0 + 0.055) ** 2.4)
    
    else:
        blue = float((blue / 12.92));

    X = red * 0.664511 + green * 0.154324 + blue * 0.162028;
    Y = red * 0.283881 + green * 0.668433 + blue * 0.047685;
    Z = red * 0.000088 + green * 0.072310 + blue * 0.986039;
    x = X / (X + Y + Z);
    y = Y / (X + Y + Z);
    return [x,y]


def GetRoom(roomName):
    jsonData = json.loads(requests.get(hueURL + "/room", headers={'hue-application-key': hueUsername},verify=False).content)
    rooms = jsonData["data"]
    for room in rooms:
        if room["metadata"]["name"] == roomName:
            return room
    
def GetAllRoomLights(room):
    deviceChildren = room["children"]
    lights = []
    for deviceChild in deviceChildren:
        device = json.loads(requests.get(hueURL + "/device/" + deviceChild["rid"], headers={'hue-application-key': hueUsername},verify=False).content)["data"][0]
        for service in device["services"]:
            if service["rtype"] == "light":
                lights.append(device)
    return lights

def GetRoomLightRID(room):
    for service in room["services"]:
        if service["rtype"] == "grouped_light":
            return service["rid"]
        
def GetLightRID(light):
    for service in light["services"]:
            if service["rtype"] == "light":
                return service["rid"]

def GetLightState(light):
    return json.loads(requests.get(hueURL + "/light/" + GetLightRID(light), headers={'hue-application-key': hueUsername},verify=False).content)["data"][0]

def SetRoomLights(room, brightness):
    roomLightRID = GetRoomLightRID(room)
    if brightness == 0:
        return requests.put(hueURL + "/grouped_light/" + roomLightRID, data = '{"on":{"on":false}}', headers={'hue-application-key': hueUsername},verify=False)
    requests.put(hueURL + "/grouped_light/" + roomLightRID, data = '{"on":{"on":true}}', headers={'hue-application-key': hueUsername},verify=False)
    return requests.put(hueURL + "/grouped_light/" + roomLightRID, data = '{"dimming":{"brightness":' + str(brightness) + '}}', headers={'hue-application-key': hueUsername},verify=False)

def SetRoomLightsColor(room, hex):
    roomLightRID = GetRoomLightRID(room)
    xy = hexToXY(hex)
    requests.put(hueURL + "/grouped_light/" + roomLightRID, data = '{"on":{"on":true}}', headers={'hue-application-key': hueUsername},verify=False)
    return requests.put(hueURL + "/grouped_light/" + roomLightRID, data = '{"color":{"xy":{"x":' + str(xy[0]) + ',"y":'+ str(xy[1]) +'}}}', headers={'hue-application-key': hueUsername},verify=False)

def SetLight(light, brightness):
    lightRID = GetLightRID(light)
    if brightness == 0:
        return requests.put(hueURL + "/light/" + lightRID, data = '{"on":{"on":false}}', headers={'hue-application-key': hueUsername},verify=False)
    requests.put(hueURL + "/light/" + lightRID, data = '{"on":{"on":true}}', headers={'hue-application-key': hueUsername},verify=False)
    return requests.put(hueURL + "/light/" + lightRID, data = '{"dimming":{"brightness":' + str(brightness) + '}}', headers={'hue-application-key': hueUsername},verify=False)

def SetLightColor(light, hex):
    lightRID = GetLightRID(light)
    xy = hexToXY(hex)
    requests.put(hueURL + "/light/" + lightRID, data = '{"on":{"on":true}}', headers={'hue-application-key': hueUsername},verify=False)
    return requests.put(hueURL + "/light/" + lightRID, data = '{"color":{"xy":{"x":' + str(xy[0]) + ',"y":'+ str(xy[1]) +'}}}', headers={'hue-application-key': hueUsername},verify=False)

room = GetRoom(hueRoomName)

class OffAllLights(rofi_menu.Item):
    """Turn off all lights"""
    def __init__(self, room, text=None, **kwargs):
            self.room = room
            super().__init__(text, **kwargs)
            
    async def on_select(self, meta):
        SetRoomLights(self.room, 0)
    
class OnAllLights(rofi_menu.Item):
    """Turn on all lights"""
    def __init__(self, room, text=None, **kwargs):
            self.room = room
            super().__init__(text, **kwargs)
            
    async def on_select(self, meta):
        SetRoomLights(self.room, 100)
        
class ToggleLight(rofi_menu.Item):
    """Toggle light"""
    def __init__(self, light, text=None, **kwargs):
        self.light = light
        self.lightState = GetLightState(self.light)
        super().__init__(text, **kwargs)
        
        
    async def on_select(self,meta):
        SetLight(self.light, 0 if self.lightState["on"]["on"] else 100)
        return rofi_menu.Operation(rofi_menu.OP_REFRESH_MENU)
        
    async def render(self, meta):
        self.lightState = GetLightState(self.light)
        offOrOn = ("off" if self.lightState["on"]["on"] else "on")
        return "Turn " + offOrOn + " light (" + self.lightState["metadata"]["name"] + ")"
    
class CustomLightColor(rofi_menu.Item):
        """Custom color button"""
        def __init__(self, light, color, text=None, **kwargs):
            self.light = light
            self.color = color
            super().__init__(text, **kwargs)
            
        async def render(self, meta):
            return self.color[0]
        
        async def on_select(self,meta):
            SetLightColor(self.light, self.color[1])
            return rofi_menu.Operation(rofi_menu.OP_BACK_TO_PARENT_MENU)
        
class CustomRoomColor(rofi_menu.Item):
        """Custom color button"""
        def __init__(self, room, color, text=None, **kwargs):
            self.room = room
            self.color = color
            super().__init__(text, **kwargs)
            
        async def render(self, meta):
            return self.color[0]
        
        async def on_select(self,meta):
            SetRoomLightsColor(self.room, self.color[1])
            return rofi_menu.Operation(rofi_menu.OP_BACK_TO_PARENT_MENU)
        
class LightControl(rofi_menu.Menu):
    """Light control menu"""
    def __init__(self, light, **kwargs):
        self.light = light
        super().__init__()
        lightToggle = ToggleLight(light)
        self.items = [rofi_menu.BackItem(), lightToggle]
        for color in colors:
            colorButton = CustomLightColor(self.light, color)
            self.items.append(colorButton)
        
class RoomColorControl(rofi_menu.Menu):
    """Room color control menu"""
    def __init__(self, room, **kwargs):
        self.room = room
        super().__init__()
        self.items = [rofi_menu.BackItem()]
        for color in colors:
            colorButton = CustomRoomColor(self.room, color)
            self.items.append(colorButton)
    


menu_items = [OnAllLights(room, text="Turn on all lights"),
        OffAllLights(room, text="Turn off all lights"), 
        rofi_menu.NestedMenu("Change room color",RoomColorControl(room))]

for light in GetAllRoomLights(room):
    lightState = GetLightState(light)
    label = (lightOnSymbol if lightState["on"]["on"] else lightOffSymbol) + " " + lightState["metadata"]["name"]
    lightControlMenu = LightControl(light)
    menu_items.append(rofi_menu.NestedMenu(label,lightControlMenu))

main_menu = rofi_menu.Menu(
    prompt="menu",
    items=menu_items,
)


if __name__ == "__main__":
    rofi_menu.run(main_menu)
import json

def get_embed_color(color_type="default"):
    with open('config.json') as f:
        config = json.load(f)
    
    colors = config["embed_colors"]
    color = colors.get(color_type, colors["default"])
    
    if isinstance(color, str):
        return int(color.replace("
    return color

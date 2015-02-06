import ConfigParser

def parse_config(section):
    configuration = {}
    config = ConfigParser.ConfigParser()
    config.read("config.ini")
    if section in config.sections():
        target_items = config.items(section)
        for setting in target_items:
            print(setting)
            configuration[setting[0]] = eval(setting[1])
    return configuration

import louie

commands = {}

def command(func, key, mode, doc):
    louie.connect(func, "%s_%s" % (key, mode))
    if doc:
        if commands.has_key(mode):
            commands[mode].append((key, doc))
        else:
            commands[mode] = [(key, doc)]

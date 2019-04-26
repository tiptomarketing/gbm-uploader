import sys

from uploader.run import run as uploader_bot
from renamer.run import run as renamer_bot


if __name__ == '__main__':
    bot = sys.argv[1]

    if bot == 'renamer':
        run = renamer_bot
    elif bot == 'uploader':
        run = uploader_bot
    else:
        raise NotImplementedError(
            "Invalid bot. \"%s\" doesn't exists." % bot
        )

    kwargs = {}

    for kwarg in sys.argv[2:]:
        try:
            k, v = kwarg.split('=')
            kwargs[k] = v
        except ValueError:
            continue

    print('Running bot "%s" with arguments "%s"' % (bot, kwargs))
    run(**kwargs)

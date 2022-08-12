import sys
import pathlib

p = pathlib.Path("fte/")
sys.path.append(str(p.absolute()))

from webapp import app  # noqa

application = app

if __name__ == "__main__":
    application.run()

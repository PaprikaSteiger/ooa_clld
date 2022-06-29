import pathlib

from clld.web.assets import environment

import ooa_clld


environment.append_path(
    str(pathlib.Path(ooa_clld.__file__).parent.joinpath('static')), url='/ooa_clld:static/')
environment.load_path = list(reversed(environment.load_path))

from pathlib import Path

from clld.web.assets import environment

import ooaclld


environment.append_path(
    Path(ooaclld.__file__).parent.joinpath('static').as_posix(),
    url='/ooaclld:static/')
environment.load_path = list(reversed(environment.load_path))

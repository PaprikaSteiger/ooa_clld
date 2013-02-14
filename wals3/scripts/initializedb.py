from __future__ import unicode_literals
import os
import sys
import transaction
from collections import defaultdict
from itertools import groupby, cycle
import re

from sqlalchemy import engine_from_config, create_engine
from path import path
from pyramid.paster import (
    get_appsettings,
    setup_logging,
    )

from clld.db.meta import (
    DBSession,
    VersionedDBSession,
    Base,
)
from clld.db.models import common

import wals3
from wals3 import models
from wals3.scripts import uncited


UNCITED_MAP = {}
for k, v in uncited.MAP.items():
    UNCITED_MAP[k.lower()] = v

#DB = 'sqlite:////home/robert/old_projects/legacy/wals_pylons/trunk/wals2/db.sqlite'
DB = create_engine('postgresql://robert@/wals')
REFDB = create_engine('postgresql://robert@/walsrefs')


class Icons(object):
    filename_pattern = re.compile('(?P<spec>(c|d|s|f|t)[0-9a-f]{3})\.png')

    def __init__(self):
        self._icons = []
        for name in sorted(path(wals3.__file__).dirname().joinpath('static', 'icons').files()):
            m = self.filename_pattern.match(name.splitall()[-1])
            if m:
                self._icons.append(m.group('spec'))

    def __iter__(self):
        return iter(self._icons)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def setup_session(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    VersionedDBSession.configure(bind=engine)


def get_source(id):
    """retrieve a source record from wals_refdb
    """
    res = {'id': id}
    refdb_id = UNCITED_MAP.get(id.lower())
    if not refdb_id:
        for row in REFDB.execute("select id, genre from ref_record, ref_recordofdocument where id = id_r_ref and citekey = '%s'" % id):
            res['genre'] = row['genre']
            refdb_id = row['id']
            break

        if not refdb_id:
            if id[-1] in ['a', 'b', 'c', 'd']:
                refdb_id = UNCITED_MAP.get(id[:-1].lower())
            if not refdb_id:
                return {}

    for row in REFDB.execute("select * from ref_recfields where id_r_ref = %s" % refdb_id):
        res[row['id_name']] = row['id_value']

    authors = ''
    for row in REFDB.execute("select * from ref_recauthors where id_r_ref = %s order by ord" % refdb_id):
        if row['type'] == 'etal':
            authors += ' et al.'
        else:
            if authors:
                authors += ' and '
            authors += row['value']
    res['authors'] = authors

    for row in REFDB.execute("select * from ref_recjournal where id_r_ref = %s" % refdb_id):
        res['journal'] = row['name']
        break

    return res


def main():
    icons = Icons()
    setup_session()
    old_db = DB

    data = defaultdict(dict)

    def add(model, type, key, **kw):
        new = model(**kw)
        data[type][key] = new
        VersionedDBSession.add(new)
        return new

    missing_sources = []
    with transaction.manager:
        with open('/home/robert/venvs/clld/data/wals-data/missing_source.py', 'w') as fp:
            for row in old_db.execute("select * from reference"):
                try:
                    author, year = row['id'].split('-')
                except:
                    author, year = None, None
                bibdata = get_source(row['id'])
                if not bibdata:
                    fp.write('"%s",\n' % row['id'])
                    missing_sources.append(row['id'])

                kw = {
                    'id': row['id'],
                    'name': row['name'],
                    'description': bibdata.get('title', bibdata.get('booktitle')),
                    'authors': bibdata.get('authors', author),
                    'year': bibdata.get('year', year),
                    'google_book_search_id': row['gbs_id'] or None,
                }
                add(common.Source, 'source', row['id'], **kw)

            #
            # TODO: add additional bibdata as data items
            #

        print('sources missing for %s refs' % len(missing_sources))

        for row in old_db.execute("select * from family"):
            add(models.Family, 'family', row['id'], id=row['id'], name=row['name'], description=row['comment'])

        for row, icon in zip(list(old_db.execute("select * from genus order by family_id")), cycle(iter(icons))):
            genus = add(models.Genus, 'genus', row['id'], id=row['id'], name=row['name'], icon_id=icon, subfamily=row['subfamily'])
            genus.family = data['family'][row['family_id']]
        VersionedDBSession.flush()

        for row in old_db.execute("select * from language"):
            kw = dict((key, row[key]) for key in ['id', 'name', 'latitude', 'longitude'])
            lang = add(models.WalsLanguage, 'language', row['id'],
                       samples_100=row['samples_100'] != 0, samples_200=row['samples_200'] != 0, **kw)
            lang.genus = data['genus'][row['genus_id']]

        for row in old_db.execute("select * from author"):
            add(common.Contributor, 'contributor', row['id'], name=row['name'], url=row['www'], id=row['id'], description=row['note'])
        VersionedDBSession.flush()

        for row in old_db.execute("select * from chapter"):
            add(models.Chapter, 'contribution', row['id'], id=row['id'], name=row['name'])
        VersionedDBSession.flush()

        for row in old_db.execute("select * from feature"):
            param = add(models.Feature, 'parameter', row['id'], id=row['id'], name=row['name'], ordinal_qualifier=row['id'][-1])
            param.chapter = data['contribution'][row['chapter_id']]
        VersionedDBSession.flush()

        for row in old_db.execute("select * from value"):
            desc = row['description']
            if desc == 'SOV & NegV/VNeg':
                if row['icon_id'] != 's9ff':
                    desc += ' (a)'
                else:
                    desc += ' (b)'

            domainelement = add(
                models.WalsValue, 'domainelement', (row['feature_id'], row['numeric']),
                id='%s-%s' % (row['feature_id'], row['numeric']),
                name=desc, description=row['long_description'], icon_id=row['icon_id'], numeric=row['numeric'])
            domainelement.parameter = data['parameter'][row['feature_id']]
        VersionedDBSession.flush()

        for row in old_db.execute("select * from datapoint"):
            value = add(common.Value, 'value', row['id'], id=row['id'])
            value.language = data['language'][row['language_id']]
            value.domainelement = data['domainelement'][(row['feature_id'], row['value_numeric'])]
            value.parameter = data['parameter'][row['feature_id']]
            value.contribution = data['parameter'][row['feature_id']].chapter

        VersionedDBSession.flush()

        for row in old_db.execute("select * from datapoint_reference"):
            common.ValueReference(
                value=data['value'][row['datapoint_id']],
                source=data['source'][row['reference_id']],
                description=row['note'],
            )

        for row in old_db.execute("select * from author_chapter"):

            new = common.ContributionContributor(
                ord=row['order'],
                primary=row['primary'] != 0,
                contributor_pk=data['contributor'][row['author_id']].pk,
                contribution_pk=data['contribution'][row['chapter_id']].pk)
            VersionedDBSession.add(new)

        lang.name = 'SPECIAL--' + lang.name


def prime_cache():
    setup_session()

    with transaction.manager:
        # cache number of languages for a parameter:
        for parameter, values in groupby(
            DBSession.query(common.Value).order_by(common.Value.parameter_pk),
            lambda v: v.parameter):

            representation = str(len(set(v.language_pk for v in values)))

            d = None
            for _d in parameter.data:
                if _d.key == 'representation':
                    d = _d
                    break

            if d:
                d.value = representation
            else:
                d = common.Parameter_data(
                    key='representation',
                    value=representation,
                    object_pk=parameter.pk)
                DBSession.add(d)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main()
    prime_cache()

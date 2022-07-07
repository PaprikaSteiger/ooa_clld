from pathlib import Path
import datetime
from collections import defaultdict

import pycldf
from tqdm import tqdm
import sqlalchemy

from clld.cliutil import Data, slug, bibtex2source, add_language_codes
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib.bibtex import Database


import ooaclld
from ooaclld import models


def main(args):

    #assert args.glottolog, 'The --glottolog option is required!'
    cldf_dir = Path(__file__).parent.parent.parent.parent / "cldf"
    # args.log.info('Loading dataset')
    ds = list(pycldf.iter_datasets(cldf_dir))[0]
    data = Data()
    data.add(
        common.Dataset,
        ooaclld.__name__,
        id=ooaclld.__name__,
        domain='ooaclld',

        publisher_name="Max Planck Institute for the Science of Human History",
        publisher_place="Jena",
        publisher_url="http://www.shh.mpg.de",
        license="http://creativecommons.org/licenses/by/4.0/",
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name': 'Creative Commons Attribution 4.0 International License'},

    )
    #DBSession.add(dataset)
    DBSession.flush()

    for rec in tqdm(Database.from_file(ds.bibpath), desc='Processing sources'):
        ns = bibtex2source(rec, common.Source)
        data.add(common.Source, ns.id, _obj=ns)
    DBSession.flush()

    for row in tqdm(ds.iter_rows('ParameterTable'), desc="Processing parameters"):
        data.add(models.OOAParameter, row["ParameterID"],
                 id=row["ParameterID"],
                 # parameter_id=row["ParameterID"],
                 # unitparameter_pk=row["ParameterID"],
                 feature_set=row["FeatureSet"],
                 question=row["Question"],
                 datatype=row["datatype"],
                 visualization=row["VisualizationOnly"],
                 )
    DBSession.flush()

    all_languages = {row["LanguageID"] for row in ds.iter_rows('ValueTable')}

    for row in tqdm(ds.iter_rows('LanguageTable'), desc='Processing languages'):
        if row["Glottocode"] not in all_languages:
            continue
        data.add(models.OOALanguage, row['Glottocode'],
                 id=row['Glottocode'],
                 glottocode=row['Glottocode'],
                 name=row['Name'],
                 latitude=row['Latitude'],
                 longitude=row['Longitude'],
                 macroarea=row['Macroarea'],
                 iso=row["ISO639P3code"],
                 family_id=row["Family_ID"],
                 language_id=row["Language_ID"],
                 family_name=row["Family_Name"],
                 balanced=row["Isolates_Balanced_Sample"],
                 isolates=row["Isolates_Sample"],
                 american=row["American_Sample"],
                 world=row["Worldwide_Sample"],
                 north_america="North_America_25_Sample",
                 noun=row["Noun_Poss_Sample"],
                 )
        DBSession.flush()

    for row in tqdm(ds.iter_rows('codes.csv'), desc="Processing codes"):
        data.add(common.DomainElement, row['CodeID'].replace(".", "").replace("]", ""),
                 id=row['CodeID'].replace(".", "").replace("]", ""),
                 description=row['Description'],
                 jsondata={'Visualization': row['Visualization']},
                 parameter_pk=data['OOAParameter'][row['ParameterID'].replace(".", "")].pk)
    DBSession.flush()

    # read value table
    for row in tqdm(ds.iter_rows('ValueTable'), desc="Processing values"):
        data.add(models.OOAUnit, row["ID"],
                 # TODO: this would be the way to refer to another resource from a table
                 # parameter = relationship('Parameter', innerjoin=True, backref='valuesets')
                 # then accessable via self.parameter.(...)
                 id=row["ID"],
                 language_pk=data["OOALanguage"][row["LanguageID"]].pk,
                 language_id=row["LanguageID"],
                 # TODO: don't do this, acces language table via language_pk to display languages
                 parameter_id=data["OOAParameter"][row["ParameterID"].replace(".", "")].pk,
                 code_id=row["CodeID"] or "",
                 value=row["Value"],
                 remark=row["Remark"],
                 source=row["Source"],
                 coder=row["Coder"],
                 )
    DBSession.flush()

    for row in tqdm(ds.iter_rows('contributors.csv'), desc="Processing contributors"):
        data.add(common.Contributor, row["ContributorID"],
                 id=row['ContributorID'],
                 name=row['Name'],
                 )

    for row in tqdm(ds.iter_rows('featuresets.csv'), desc='Processing featuresets'):
        data.add(models.OOAFeatureSet, row["FeatureSetID"],
                 unitparameter_pk=row["FeatureSetID"],
                 id=row['FeatureSetID'],
                 name=row['Name'],
                 domains=row['Domain'],
                 authors=";".join(row['Authors']),
                 contributors=";".join(row['Contributors'] or [""]),
                 filename=row['Filename'] or ""
                 )

    # contrib = data.add(
    #     common.Contribution,
    #     None,
    #     id='cldf',
    #     name=args.cldf.properties.get('dc:title'),
    #     description=args.cldf.properties.get('dc:bibliographicCitation'),
    # )
    #
    # for lang in args.cldf.iter_rows('LanguageTable', 'id', 'glottocode', 'name', 'latitude', 'longitude'):
    #     data.add(
    #         models.Variety,
    #         lang['id'],
    #         id=lang['id'],
    #         name=lang['name'],
    #         latitude=lang['latitude'],
    #         longitude=lang['longitude'],
    #         glottocode=lang['glottocode'],
    #     )
    #
    # for rec in bibtex.Database.from_file(args.cldf.bibpath, lowercase=True):
    #     data.add(common.Source, rec.id, _obj=bibtex2source(rec))
    #
    # refs = collections.defaultdict(list)
    #
    #
    # for (vsid, sid), pages in refs.items():
    #     DBSession.add(common.ValueSetReference(
    #         valueset=data['ValueSet'][vsid],
    #         source=data['Source'][sid],
    #         description='; '.join(nfilter(pages))
    #     ))
    # load_families(
    #     Data(),
    #     [(l.glottocode, l) for l in data['Variety'].values()],
    #     glottolog_repos=args.glottolog,
    #     isolates_icon='tcccccc',
    #     strict=False,
    # )



def prime_cache(args):
    """If data needs to be denormalized for lookup, do that here.
    This procedure should be separate from the db initialization, because
    it will have to be run periodically whenever data has been updated.
    """

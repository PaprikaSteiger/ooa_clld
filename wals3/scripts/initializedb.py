from pathlib import Path
import datetime
from collections import defaultdict

import pycldf
from tqdm  import tqdm
import sqlalchemy

from clld.cliutil import Data, slug, bibtex2source, add_language_codes
from clld.db.meta import DBSession
from clld.db.models import common
from clld.lib.bibtex import Database

from wals3 import models

def main(args):
    cldf_dir = Path(r"C:\Users\steig\Desktop\outofasia\wals3\cldf")
    #args.log.info('Loading dataset')
    ds = list(pycldf.iter_datasets(cldf_dir))[0]
    data = Data()

    dataset = common.Dataset(
        id='wals',
        name='WALS Online',
        description=ds.properties['dc:title'],
        published=datetime.date(2013, 8, 15),
        publisher_name="Max Planck Institute for Evolutionary Anthropology",
        publisher_place="Leipzig",
        publisher_url="https://www.eva.mpg.de",
        license=ds.properties['dc:license'],
        contact='wals@shh.mpg.de',
        jsondata={
            'license_icon': 'cc-by.png',
            'license_name':
                'Creative Commons Attribution 4.0 International License',
        },
        domain=ds.properties['dc:identifier'].split('://')[1])
    DBSession.add(dataset)
    DBSession.flush()

    for rec in tqdm(Database.from_file(ds.bibpath), desc='Processing sources'):
        ns = bibtex2source(rec, common.Source)
        data.add(common.Source, ns.id, _obj=ns)
    DBSession.flush()

    for row in tqdm(ds.iter_rows('ParameterTable'), desc="Processing parameters"):
        data.add(models.OOAParameter, row["ParameterID"],
                 id=row["ParameterID"],
                 #parameter_id=row["ParameterID"],
                 unitparameter_pk=row["ParameterID"],
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
                 id=row["ID"],
                 language_pk=data["OOALanguage"][row["LanguageID"]].pk,
                 language_id=row["LanguageID"],
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
                 id=row['FeatureSetID'],
                 name=row['Name'],
                 domains=row['Domain'],
                 authors=";".join(row['Authors']),
                 contributors=";".join(row['Contributors'] or [""]),
                 filename=row['Filename'] or ""


        )
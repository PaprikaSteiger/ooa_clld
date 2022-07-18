from sqlalchemy.orm import joinedload, contains_eager, subqueryload

from clld.web import datatables
from clld.web.datatables.base import Col, LinkCol, DetailsRowLinkCol, IdCol, DataTable
from clld.web.datatables import Units
from clld.web.datatables.value import ValueNameCol
from clld.db.meta import DBSession
from clld.db.models import common
from clld.db.util import get_distinct_values, icontains
from clld.web.util.helpers import linked_contributors, link, contactmail
from clld.web.util.htmllib import HTML

from ooaclld.models import OOALanguage, OOAParameter, OOAUnit, OOAFeatureSet


class Features(datatables.Parameters):
    # def base_query(self, query):
    #     return query.join(Chapter).join(Area)\
    #         .options(contains_eager(Feature.chapter, Chapter.area))

    # def col_defs(self):
    #     return [
    #         FeatureIdCol(self, 'id', sClass='right'),
    #         LinkCol(self, 'name'),
    #         ContributorsCol(self, 'Authors', bSearchable=False, bSortable=False),
    #         FeatureAreaCol(self, 'area'),
    #         Col(self, 'Languages', model_col=Feature.representation),
    #         DetailsRowLinkCol(self, 'd', button_text='Values'),
    #     ]
    def col_defs(self):
        return [
            IdCol(self, 'id', sClass='left'),
            Col(self, 'FeatureSet', model_col=OOAParameter.feature_set),
            Col(self, 'Questions', model_col=OOAParameter.question),
            Col(self, 'Visualization', model_col=OOAParameter.visualization),
            Col(self, 'Datatype', model_col=OOAParameter.datatype),
        ]


class Featuresets(datatables.Unitparameters):
    def col_defs(self):
        return [
            IdCol(self, 'id', sClass='left'),
            Col(self, 'Domains', model_col=OOAFeatureSet.domains),
            Col(self, 'Authors', model_col=OOAFeatureSet.authors),
            Col(self, 'Contributors', model_col=OOAFeatureSet.contributors),
            Col(self, 'Filename', model_col=OOAFeatureSet.filename),
        ]


class Languages(datatables.Languages):
    def col_defs(self):
        return [
            IdCol(self, 'id', sTitle='glottocode', sClass='left'),
            Col(self, 'macroarea', model_col=OOALanguage.macroarea),
            Col(self, 'family_id', model_col=OOALanguage.family_id)
        ]


class Units(Units):

    def base_query(self, query):
        if self.language:
            query = query.join(OOALanguage, self.language_pk == self.language.pk)
        return query

    def col_defs(self):
        return [
            IdCol(self, 'id', sTitle='id'),
            Col(self, 'parameter_id', model_col=OOAUnit.parameter_id),
            Col(self, 'language_id', model_col=OOAUnit.language_pk)
        ]
# class Languages(datatables.Languages):
#     def base_query(self, query):
#         return query.join(Genus).join(Family).options(
#             contains_eager(WalsLanguage.genus, Genus.family),
#             subqueryload(WalsLanguage.countries))
#
#     def col_defs(self):
#         return [
#             LinkCol(self, 'name'),
#             IdCol(self, 'id', sTitle='WALS code', sClass='left'),
#             Col(self, 'iso_codes', sTitle='ISO 639-3', model_col=WalsLanguage.iso_codes),
#             LinkCol(self, 'genus', model_col=Genus.name, get_object=lambda i: i.genus),
#             LinkCol(self, 'family',
#                     model_col=Family.name,
#                     get_object=lambda i: i.genus.family),
#             Col(self, 'macroarea',
#                 model_col=WalsLanguage.macroarea,
#                 choices=get_distinct_values(WalsLanguage.macroarea)),
#             Col(self, 'latitude'),
#             Col(self, 'longitude'),
#             CountriesCol(self, 'countries'),
#         ]


def includeme(config):
    # the name of the datatable must be the same as the name given to the route pattern
    config.register_datatable('units', Units)
    config.register_datatable('languages', Languages)
    config.register_datatable('parameters', Features)
    config.register_datatable('featuresets', Featuresets)


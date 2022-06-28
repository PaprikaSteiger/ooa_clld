from zope.interface import implementer
from sqlalchemy import (
    Column,
    String,
    Unicode,
    Integer,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, backref

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models.common import (
    Language,
    Parameter,
    Value,
    Contribution,
    IdNameDescriptionMixin,
    ValueSet,
    Unit,
    Contributor,
    UnitDomainElement
)
from wals3 import interfaces as wals_interfaces


ValueSet.wp_slug = property(lambda self: 'datapoint-%s-wals_code_%s' % (
    self.parameter.id.lower(), self.language.id))


@implementer(wals_interfaces.IFamily)
class Family(Base, IdNameDescriptionMixin):
    pass


class CountryLanguage(Base):
    __table_args__ = (UniqueConstraint('country_pk', 'language_pk'),)

    country_pk = Column(Integer, ForeignKey('country.pk'))
    language_pk = Column(Integer, ForeignKey('language.pk'))


@implementer(wals_interfaces.ICountry)
class Country(Base, IdNameDescriptionMixin):
    continent = Column(Unicode)
    languages = relationship(
        Language, secondary=CountryLanguage.__table__, backref='countries')


@implementer(wals_interfaces.IGenus)
class Genus(Base, IdNameDescriptionMixin):
    family_pk = Column(Integer, ForeignKey('family.pk'))
    subfamily = Column(Unicode)
    family = relationship(
        Family, backref=backref("genera", order_by="Genus.subfamily, Genus.name"))
    icon = Column(String(7))


class Area(Base, IdNameDescriptionMixin):
    dbpedia_url = Column(String)


# ----------------------------------------------------------------------------
# specialized common mapper classes
# ----------------------------------------------------------------------------
@implementer(interfaces.ILanguage)
class OOALanguage(CustomModelMixin, Language):
    pk = Column(Unicode, ForeignKey('language.pk'), primary_key=True)
    glottocode = Column(Unicode)
    macroarea = Column(Unicode)
    iso = Column(Unicode)
    family_id = Column(Unicode)
    language_id = Column(Unicode)
    family_name = Column(Unicode)
    balanced = Column(Unicode)
    isolates = Column(Unicode)
    american = Column(Unicode)
    world = Column(Unicode)
    north_america = Column(Unicode)
    noun = Column(Unicode)


# @implementer(interfaces.ILanguage)
# class WalsLanguage(CustomModelMixin, Language):
#     pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
#
#     ascii_name = Column(String)
#     genus_pk = Column(Integer, ForeignKey('genus.pk'))
#     samples_100 = Column(Boolean, default=False)
#     samples_200 = Column(Boolean, default=False)
#
#     macroarea = Column(Unicode)
#     iso_codes = Column(String)
#     genus = relationship(Genus, backref=backref("languages", order_by="Language.name"))
#
#     def __rdf__(self, request):
#         yield 'skos:broader', request.resource_url(self.genus)
#         if self.macroarea:
#             yield 'dcterms:spatial', self.macroarea
#         for country in self.countries:
#             yield 'dcterms:spatial', 'http://www.geonames.org/countries/%s/' % country.id


@implementer(interfaces.IContribution)
class Chapter(CustomModelMixin, Contribution):

    """Contributions in WALS are chapters chapters.

    These comprise a set of features with corresponding values and a descriptive text.
    """

    pk = Column(Integer, ForeignKey('contribution.pk'), primary_key=True)
    sortkey = Column(Integer)
    wp_slug = Column(Unicode)
    area_pk = Column(Integer, ForeignKey('area.pk'))
    area = relationship(Area, lazy='joined')

    def __rdf__(self, request):
        if self.area and self.area.dbpedia_url:
            yield 'dcterms:subject', self.area.dbpedia_url


@implementer(interfaces.IParameter)
class OOAParameter(CustomModelMixin, Parameter):

    """TODO"""

    #__table_args__ = (UniqueConstraint('contribution_pk', 'ordinal_qualifier'),)

    pk = Column(Unicode, ForeignKey('parameter.pk'), primary_key=True)
    #parameter_id = Column(Unicode)
    feature_set = Column(Unicode) # Column(Integer, ForeignKey('featureset.pk'))
    question = Column(Unicode)
    datatype = Column(Unicode)
    visualization = Column(Unicode)

# TODO: Implement featuresets like this
# @implementer(wals_interfaces.IFeatureset)
# class OOAFeatureSet((Base,
#                PolymorphicBaseMixin,
#                Versioned,
#                IdNameDescriptionMixin,
#                HasDataMixin,
#                HasFilesMixin)):
# TODO: add those functions for featureset
# class ValueSet_data(Base, Versioned, DataMixin):
#     pass
#
#
# class ValueSet_files(Base, Versioned, FilesMixin):
#     pass

@implementer(interfaces.IUnitDomainElement)
class OOAFeatureSet(CustomModelMixin, UnitDomainElement):
    pk = Column(Unicode, ForeignKey('unitdomainelement.pk'), primary_key=True)

    domains = Column(Unicode)
    authors = Column(Unicode)
    contributors = Column(Unicode)
    filename = Column(Unicode)
# @implementer(interfaces.IParameter)
# class Feature(CustomModelMixin, Parameter):
#
#     """Parameters in WALS are called feature. They are always related to one chapter."""
#
#     __table_args__ = (UniqueConstraint('contribution_pk', 'ordinal_qualifier'),)
#
#     pk = Column(Integer, ForeignKey('parameter.pk'), primary_key=True)
#     contribution_pk = Column(Integer, ForeignKey('contribution.pk'))
#     blog_title = Column(String(50), unique=True)
#     representation = Column(Integer)
#     chapter = relationship(Chapter, lazy='joined', backref="features")
#     ordinal_qualifier = Column(String)
#
#     def __rdf__(self, request):
#         if self.chapter.area.dbpedia_url:
#             yield 'dcterms:subject', self.chapter.area.dbpedia_url

@implementer(interfaces.IUnit)
class OOAUnit(CustomModelMixin, Unit):
    pk = Column(Unicode, ForeignKey('unit.pk'), primary_key=True)

    language_id = Column(Unicode, ForeignKey('language.pk'))
    parameter_id = Column(Unicode, ForeignKey('parameter.pk'))
    code_id = Column(Unicode)
    value = Column(Unicode)
    remark = Column(Unicode)
    source = Column(Unicode, ForeignKey('source.pk'))
    coder = Column(Unicode)

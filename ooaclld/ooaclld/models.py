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
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

from clld import interfaces
from clld.db.meta import Base, CustomModelMixin
from clld.db.models import common

from ooaclld import interfaces as ooaclld_interfaces

from clld_glottologfamily_plugin.models import HasFamilyMixin


#-----------------------------------------------------------------------------
# specialized common mapper classes
#-----------------------------------------------------------------------------

# @implementer(interfaces.ILanguage)
# class Variety(CustomModelMixin, common.Language, HasFamilyMixin):
#     pk = Column(Integer, ForeignKey('language.pk'), primary_key=True)
#     glottocode = Column(Unicode)


@implementer(interfaces.ILanguage)
class OOALanguage(CustomModelMixin, common.Language):
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


@implementer(interfaces.IParameter)
class OOAParameter(CustomModelMixin, common.Parameter):

    """TODO"""

    #__table_args__ = (UniqueConstraint('contribution_pk', 'ordinal_qualifier'),)

    pk = Column(Unicode, ForeignKey('parameter.pk'), primary_key=True)
    #parameter_id = Column(Unicode)
    feature_set = Column(Unicode) # Column(Integer, ForeignKey('featureset.pk'))
    question = Column(Unicode)
    datatype = Column(Unicode)
    visualization = Column(Unicode)


@implementer(ooaclld_interfaces.IFeatureSet)
class OOAFeatureSet(CustomModelMixin, common.UnitDomainElement):
    pk = Column(Unicode, ForeignKey('unitdomainelement.pk'), primary_key=True)
    domains = Column(Unicode)
    authors = Column(Unicode)
    contributors = Column(Unicode)
    filename = Column(Unicode)


@implementer(interfaces.IUnit)
class OOAUnit(CustomModelMixin, common.Unit):
    pk = Column(Unicode, ForeignKey('unit.pk'), primary_key=True)

    language_id = Column(Unicode, ForeignKey('language.pk'))
    parameter_id = Column(Unicode, ForeignKey('parameter.pk'))
    code_id = Column(Unicode)
    value = Column(Unicode)
    remark = Column(Unicode)
    source = Column(Unicode, ForeignKey('source.pk'))
    coder = Column(Unicode)

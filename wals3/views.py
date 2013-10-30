from datetime import datetime
from itertools import groupby

from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload_all, joinedload
from sqlalchemy.inspection import inspect
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPMovedPermanently, HTTPFound
from pytz import utc

from clld.db.meta import DBSession
from clld.db.models.common import Value, ValueSet, Source
from clld.web.views.olac import OlacConfig, olac_with_cfg, Participant, Institution
from wals3.models import Family, Genus, Feature


@view_config(route_name='feature_info', renderer='json')
def info(request):
    feature = Feature.get(request.matchdict['id'])
    return {
        'name': feature.name,
        'values': [{'name': d.name, 'number': i + 1} for i, d in enumerate(feature.domain)],
    }


@view_config(route_name='datapoint', request_method='POST')
def comment(request):
    """
    check whether a blog post for the datapoint does exist, if not, create one and
    redirect there.
    """
    vs = ValueSet.get('%(fid)s-%(lid)s' % request.matchdict)
    return HTTPFound(request.blog.post_url(vs, request, create=True) + '#comment')


@view_config(route_name='genealogy', renderer='genealogy.mako')
def genealogy(request):
    return dict(
        families=DBSession.query(Family).order_by(Family.id)\
        .options(joinedload_all(Family.genera, Genus.languages)))


def changes(request):
    """
    select vs.id, v.updated, h.domainelement_pk, v.domainelement_pk from value_history as h, value as v, valueset as vs where h.pk = v.pk and v.valueset_pk = vs.pk;
    """
    # changes in the 2011 edition: check values with an updated date after 2011 and before 2013
    E2009 = utc.localize(datetime(2009, 1, 1))
    E2012 = utc.localize(datetime(2012, 1, 1))

    history = inspect(Value.__history_mapper__).class_
    query = DBSession.query(Value, history)\
        .join(ValueSet)\
        .filter(Value.pk == history.pk)\
        .order_by(ValueSet.parameter_pk, ValueSet.language_pk)\
        .options(joinedload_all(Value.valueset, ValueSet.language))

    changes2011 = query.filter(or_(
        and_(E2009 < Value.updated, Value.updated < E2012),
        and_(E2009 < history.updated, history.updated < E2012)))

    changes2013 = query.filter(or_(
        E2012 < Value.updated, E2012 < history.updated))

    return {
        'changes2011': groupby([v.valueset for v, h in changes2011], lambda vs: vs.parameter),
        'changes2013': groupby([v.valueset for v, h in changes2013], lambda vs: vs.parameter)}


@view_config(route_name='sample', renderer='sample.mako')
def sample(ctx, request):
    return {'ctx': ctx}


class OlacConfigSource(OlacConfig):
    def _query(self, req):
        return req.db.query(Source)

    def get_earliest_record(self, req):
        return self._query(req).order_by(Source.updated, Source.pk).first()

    def get_record(self, req, identifier):
        """
        """
        rec = Source.get(self.parse_identifier(req, identifier), default=None)
        assert rec
        return rec

    def query_records(self, req, from_=None, until=None):
        q = self._query(req).order_by(Source.pk)
        if from_:
            q = q.filter(Source.updated >= from_)
        if until:
            q = q.filter(Source.updated < until)
        return q

    def format_identifier(self, req, item):
        """
        """
        return self.delimiter.join([self.scheme, 'refdb.' + req.dataset.domain, str(item.pk)])

    def parse_identifier(self, req, id_):
        """
        """
        assert self.delimiter in id_
        return int(id_.split(self.delimiter)[-1])

    def description(self, req):
        return {
            'archiveURL': 'http://%s/refdb_oai' % req.dataset.domain,
            'participants': [
                Participant("Admin", 'Robert Forkel', 'robert_forkel@eva.mpg.de'),
            ] + [Participant("Editor", ed.contributor.name, ed.contributor.email or req.dataset.contact) for ed in req.dataset.editors],
            'institution': Institution(
                req.dataset.publisher_name,
                req.dataset.publisher_url,
                '%s, Germany' % req.dataset.publisher_place,
            ),
            'synopsis': 'The World Atlas of Language Structures Online is a large database '
            'of structural (phonological, grammatical, lexical) properties of languages '
            'gathered from descriptive materials (such as reference grammars). The RefDB '
            'archive contains bibliographical records for all resources cited in WALS Online.',
        }


@view_config(route_name='olac.source')
def olac_source(req):
    return olac_with_cfg(req, OlacConfigSource())

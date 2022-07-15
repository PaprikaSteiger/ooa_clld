import string
import itertools

from sqlalchemy import true
from sqlalchemy.orm import joinedload
from pyramid.httpexceptions import HTTPNotFound, HTTPMovedPermanently
from pyramid.config import Configurator
from pyramid.response import Response

from clldutils import svg
from clld.interfaces import (
    IParameter, IMapMarker, IDomainElement, IValue, ILanguage,
    ICtxFactoryQuery, IIconList, IUnit, IUnitParameter
)
from clld.web.adapters.download import Download
from clld.web.adapters.base import adapter_factory
from clld.web.icon import Icon
from clld.web.app import CtxFactoryQuery, ClldRequest
from clld.db.models.common import Contribution, ContributionReference, Parameter, Language, Source, DomainElement

from wals3.adapters import Matrix
from wals3.models import Family, Country, Genus, OOALanguage, OOAParameter, OOAUnit, OOAFeatureSet
from wals3.interfaces import IFamily, ICountry, IGenus, IFeatureSet
from wals3.datatables import Featuresets

COLORS = [
    '00d', '000', '6f3', '9ff', '090', '99f', '909', 'a00', 'ccc', 'd00', 'f6f', 'f40', 'f60',
    'fc0', 'ff0', 'ffc', 'fff']
SHAPES = list('cdfst')


_ = lambda s: s
_('Contributions')
_('Contributors')
_('Contributor')
_('Sources')
_('Source')
_('Parameters')
_('Parameter')
_('ValueSets')
_('Sentences')


def map_marker(ctx, req):
    """allow for user-selectable markers.

    we have to look up a possible custom selection from the url params.
    """
    icon = None

    if IValue.providedBy(ctx):
        icon = req.params.get(
            'v%s' % ctx.domainelement.number,
            ctx.domainelement.jsondata['icon'])
    elif IDomainElement.providedBy(ctx):
        icon = req.params.get('v%s' % ctx.number, ctx.jsondata['icon'])
    elif ILanguage.providedBy(ctx):
        # hard coded icon
        icon = req.params.get(ctx.id, 'c0000dd')
        #icon = req.params.get(ctx.id, ctx.genus.icon)
    elif isinstance(ctx, Genus):
        icon = req.params.get(ctx.id, ctx.icon)

    if icon:
        if "'" in icon:
            icon = icon.split("'")[0]
        if len(icon) > 4 and len(icon) != 7:
            icon = icon[:4]
        if len(icon) == 4:
            icon = icon[0] + 2*icon[1] + 2*icon[2] + 2*icon[3]
        if icon.startswith('a'):
            return svg.data_url(svg.icon('c000000', opacity='0'))
        try:
            return svg.data_url(svg.icon(icon))
        except KeyError:
            return ''


class WalsCtxFactoryQuery(CtxFactoryQuery):
    def refined_query(self, query, model, req):
        if model == Contribution:
            return query.options(
                joinedload(Contribution.references).joinedload(ContributionReference.source))
        if model == Parameter:
            if req.matchdict['id'][-1] not in string.ascii_uppercase:
                # route match for 2008-style URL: redirect!
                raise HTTPMovedPermanently(
                    req.route_url('parameters', id=req.matchdict['id']))
        if model == Source:
            try:
                # redirect legacy refdb URLs formed with numeric id:
                rec = Source.get(int(req.matchdict['id']), default=None)
                if rec:
                    raise HTTPMovedPermanently(
                        req.route_url('source', id=rec.id))
                else:
                    raise HTTPNotFound()
            except ValueError:
                pass
        return query


def sample_factory(req):
    class Sample(object):
       # name = '%s-language sample' % req.matchdict['count']
        languages = req.db.query(OOALanguage).all()
            # .filter(col == true())\
            # .options(joinedload(WalsLanguage.genus).joinedload(Genus.family))\
            # .order_by(WalsLanguage.name)

        def __json__(self, req):
            return {'name': self.name, 'languages': list(self.languages)}

    return Sample()


def codes_sample_factory(req):
    class Sample(object):
        codes = req.db.query(DomainElement).all()

        # .filter(col == true())\
        # .options(joinedload(WalsLanguage.genus).joinedload(Genus.family))\
        # .order_by(WalsLanguage.name)

        def __json__(self, req):
            return {'codes': list(self.codes)}

    return Sample()


# def featureset_sample_factory(req: ClldRequest):
#     class Sample(object):
#         featuresets = req.db.query(OOAFeatureSet).all()
#         table = req.get_datatable(name='featuresets', model=OOAFeatureSet)
#
#         def __json__(self, req):
#             return {'req': req, 'featuresets': list(self.featuresets), 'table': self.table}
#
#     return Sample()

class WalsIcon(Icon):
    def url(self, req):
        return svg.data_url(svg.icon(self.name))


def main(global_config, **settings):
    """return a Pyramid WSGI application."""
    settings['route_patterns'] = {
        'languages': r'/ooalanguages',
        'language': r'/ooalanguages/{id:[^/\.]+}',
        'source': r'/refdb/record/{id:[^/\.]+}',
        'sources': '/refdb',
        #'familys': '/languoid/family',
        #'family': r'/languoid/family/{id:[^/\.]+}',
        #'genus': r'/languoid/genus/{id:[^/\.]+}',
        'parameters': '/ooafeatures',
        'parameter': r'/ooafeatures/{id:[^/\.]+}',
        'featuresets': r'/ooafeaturesets',
        'featureset': r'/ooafeaturesets/{id:[^/\.]+}',
        #'sentences': '/example',
        #'sentence': r'/example/{id:[^/\.]+}',
        # 'contributions': '/chapter',
        # 'contribution': r'/chapter/{id:[^/\.]+}',
        # 'countrys': '/country',
        # 'country': r'/country/{id:[^/\.]+}',
        # 'contributors': '/author',
        # 'contributor': r'/author/{id:[^/\.]+}',
        # 'legal': '/about/legal',
        # 'olac': '/languoid/oai',
        # 'credits': '/about/credits',
        'codes': r'/domainelement',
        'code': r'/domainelement/{id}',
        'units': r'/ooaunits',
        'unit': r'/ooaunits/{id}'
    }
    icons = [WalsIcon(s + c) for s, c in itertools.product(SHAPES, COLORS)]

    #config = Configurator(**dict(settings=settings))
    config = Configurator(**dict(settings=settings))
    config.include('clldmpg')
    for utility, interface in [
        (WalsCtxFactoryQuery(), ICtxFactoryQuery),
        (map_marker, IMapMarker),
        (icons, IIconList),
    ]:
        config.registry.registerUtility(utility, interface)
    # TODO: register_resource and add_route provoke pyramid.exceptions.ConfigurationConflictError: Conflicting configuration actions
    # config.register_resource('family', Family, IFamily, with_index=True)
    # config.register_resource('genus', Genus, IGenus, with_index=True)
    # config.register_resource('country', Country, ICountry)
    config.register_resource('ooalanguage', OOALanguage, ILanguage)
    config.register_resource('ooafeature', OOAParameter, IParameter)
    config.register_resource('ooacodes', DomainElement, IDomainElement)
    config.register_resource('ooaunit', OOAUnit, IUnit)
    config.register_resource('ooafeaturesets', OOAFeatureSet, IFeatureSet)
    # this should register the values template as an adapter for Iunit
    # config.register_adapter(adapter_factory('values/lib.mako'), IUnit)
    # config.add_route(
    #     'sample_alt', '/languoid/samples/{count}.{ext}', factory=sample_factory)
    # config.add_route(
    #     'sample', '/languoid/samples/{count}', factory=sample_factory)
    #
    # config.add_route('olac.source', '/refdb_oai')
    # config.add_route('languoids', '/languoids')
    # config.add_route('languages', '/ooalanguages', factory=sample_factory)
    # config.add_route('units', '/ooaunits')
    # TODO: without those lines, KeyError: 'No such route named features'
    # TODO: so what does settings even do?
    config.add_route('features', '/ooafeatures')
    config.add_route('codes', '/domainelement', factory=codes_sample_factory)
    config.add_route('featuresets', '/ooafeaturesets',)
    # this is required to display the featuresets as they are mapped to unitdomainelements
    config.add_route('unitdomainelements', '/ooafeaturesets')
    # for spec in [
    #     dict(
    #         template='parameter/detail_tab.mako',
    #         mimetype='application/vnd.clld.tab',
    #         send_mimetype="text/plain",
    #         extension='tab',
    #         name='tab-separated values'),
    #     dict(
    #         template='parameter/detail_xml.mako',
    #         mimetype='application/vnd.clld.xml',
    #         send_mimetype="application/xml",
    #         extension='xml',
    #         name='WALS XML',
    #         __doc__="Custom XML format."),
    #     dict(
    #         template='parameter/detail_georss.mako',
    #         mimetype='application/vnd.clld.georss+xml',
    #         send_mimetype="application/rdf+xml",
    #         extension='georss',
    #         name="GeoRSS",
    #         __doc__="RSS with location information "
    #                 "(http://en.wikipedia.org/wiki/GeoRSS)."),
    #     dict(
    #         template='parameter/detail_kml.mako',
    #         mimetype='application/vnd.google-earth.kml+xml',
    #         send_mimetype="application/xml",
    #         extension='kml',
    #         name='KML',
    #         __doc__="Keyhole Markup Language"),
    # ]:
    #     config.register_adapter(spec, IParameter)
    #
    # config.add_route('feature_info', '/feature-info/{id}')
    # config.add_route('genealogy', '/languoid/genealogy')
    #
    # config.add_301(
    #     '/index',
    #     lambda req: req.route_url('dataset'))
    # config.add_301(
    #     '/.{ext}',
    #     lambda req: req.route_url('dataset_alt', ext=req.matchdict['ext']))
    # config.add_301(
    #     '/example/{fid}/all',
    #     lambda req: req.route_url('parameter', id=req.matchdict['fid']))
    # config.add_301(
    #     '/example/all/wals_code_{lid}',
    #     lambda req: req.route_url(
    #         'sentences', _query=dict(language=req.matchdict['lid'])))

    # we redirect legacy urls for datapoints because they could not be expressed
    # with a single id.
    # def datapoint(req):
    #     data = {k: v for k, v in req.matchdict.items()}
    #     if data['fid'][-1] not in string.ascii_uppercase:
    #         data['fid'] += 'A'
    #     return req.route_url(
    #         'valueset', id='%(fid)s-%(lid)s' % data, _query=req.query_params)
    #
    # config.add_301('/datapoint/{fid}/wals_code_{lid}', datapoint, name='datapoint')
    #
    # # we redirect legacy urls for feature combinations because they could not be expressed
    # # with a single id.
    # def combined(req):
    #     return req.route_url(
    #         'combination', id='%(id1)s_%(id2)s' % req.matchdict, _query=req.query_params)
    #
    # config.add_301('/feature/combined/{id1}/{id2}', combined, name='combined')
    #
    # config.add_301(
    #     "/feature/description/{id:[0-9]+}",
    #     lambda req: req.route_url('parameters', id=req.matchdict['id']))
    #
    # config.add_301(
    #     "/languoid/by_geography",
    #     lambda req: req.route_url('country', id=req.params.get('country')))
    #
    # config.add_301(
    #     "/wals-2011-{fid}",
    #     lambda req: req.route_url('parameter', id=req.matchdict.get('fid')))
    #
    # config.add_301('/languoid/lect', lambda req: req.route_url('languages'))
    # config.add_301('/languoid/family', lambda req: req.route_url('languages'))
    # config.add_301('/languoid/genus', lambda req: req.route_url('languages'))
    # config.add_301('/supplement/1', lambda req: req.route_url('contribution', id='s1'))
    # config.add_301('/supplement/3', lambda req: req.route_url('contribution', id='s1'))
    # config.add_301('/supplement/5', lambda req: req.route_url('contribution', id='s5'))
    # config.add_301('/supplement/6', lambda req: req.route_url('contribution', id='s6'))
    # config.add_301('/supplement/7', lambda req: req.route_url('contribution', id='s7'))
    # config.add_301('/supplement/8', lambda req: req.route_url('contribution', id='s8'))
    # config.add_301('/supplement/9', lambda req: req.route_url('contribution', id='s9'))
    #
    # def notfound(request):
    #     print(request)
    #     return Response('Not Found', status='404 Not Found')
    #
    #
    # config.add_notfound_view(notfound)
    #
    # for pattern in ['/refdb/', '/refdb/record', '/refdb/record/', '/refdb/search']:
    #     config.add_301(pattern, lambda req: req.route_url('sources'))
    #
    # config.add_410('/languoid/osd.{ext}')
    # config.add_410("/experimental/{id}")
    #
    #
    # config.register_download(
    #     Matrix(Language, 'wals3', description="Feature values CSV"))
    # config.register_download(
    #     Download(Source, 'wals3', ext='bib', description="Sources as BibTeX"))

    return config.make_wsgi_app()

import collections

from pyramid.config import Configurator

from clld_glottologfamily_plugin import util

from clldutils import svg
from clld.interfaces import IMapMarker, IValueSet, IValue, IDomainElement, ILanguage, IParameter
from clldutils.svg import pie, icon, data_url
from clld.web.adapters.base import adapter_factory
from clld.web.app import ClldRequest

# we must make sure custom models are known at database initialization!
from ooaclld import models
from ooaclld.interfaces import IFeatureSet


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


class LanguageByFamilyMapMarker(util.LanguageByFamilyMapMarker):
    def __call__(self, ctx, req):
    
        return super(LanguageByFamilyMapMarker, self).__call__(ctx, req)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['route_patterns'] = {
    }
    config = Configurator(settings=settings)

    config.include('clld.web.app')

    config.include('clldmpg')

    config.register_resource('featureset', models.OOAFeatureSet, IFeatureSet, with_index=True)

    config.registry.registerUtility(LanguageByFamilyMapMarker(), IMapMarker)

    return config.make_wsgi_app()

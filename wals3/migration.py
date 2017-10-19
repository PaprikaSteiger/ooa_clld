from __future__ import unicode_literals

import string
import unicodedata

from six import string_types

from clld.db.models.common import (
    Identifier, LanguageIdentifier, Language, IdentifierType, Source,
)
from clld.db.migration import Connection as BaseConnection

from wals3.models import Family, Genus, WalsLanguage


def ascii_name(s, _whitelist=set(string.ascii_lowercase + ' ()0123456789')):
    """

    >>> print(ascii_name('Bobo Madar\xe9 (Northern)'))
    bobo madare (northern)

    >>> print(ascii_name('Chumash (Barbare\xf1o)'))
    chumash (barbareno)
    """
    s = ''.join(c for c in unicodedata.normalize('NFD', s)
                if not unicodedata.combining(c))
    return ''.join(c for c in s.lower() if c in _whitelist)


class Connection(BaseConnection):
    def insert_if_missing(self, model, where, values=None):
        values = values or {}
        row = self.first(model, **where)
        if row:
            return row.pk
        values.update(where)
        return self.insert(model, **values)

    def update_glottocode(self, lid, gc):
        lpk = self.pk(Language, lid)

        for li in self.select(LanguageIdentifier, language_pk=lpk):
            i = self.get(Identifier, li.identifier_pk)
            if i.type == 'glottolog':
                self.update(Identifier, dict(name=gc), pk=i.pk)
                break
        else:
            ipk = self.insert_if_missing(
                Identifier,
                dict(id=gc),
                dict(name=gc, description=gc, type='glottolog'))
            self.insert(LanguageIdentifier, identifier_pk=ipk, language_pk=lpk)

    def update_iso(self, lid, *obsolete, **new):  # pragma: no cover
        lpk = self.pk(Language, lid)

        for _code in obsolete:
            for code in [_code, 'ethnologue-' + _code]:
                i = self.pk(Identifier, code)
                li = self.first(LanguageIdentifier, identifier_pk=i, language_pk=lpk)
                if li:
                    self.delete(LanguageIdentifier, pk=li.pk)

        for code, name in new.items():
            ipk = self.insert_if_missing(
                Identifier,
                dict(id=code),
                dict(name=code, description=name, type=IdentifierType.iso.value))
            self.insert_if_missing(
                LanguageIdentifier, dict(identifier_pk=ipk, language_pk=lpk))

            ipk = self.insert_if_missing(
                Identifier,
                dict(id='ethnologue-' + code),
                dict(name=name, description='ethnologue', type='name'))
            self.insert_if_missing(
                LanguageIdentifier, dict(identifier_pk=ipk, language_pk=lpk))
        return lpk

    def update_genus(self, lid, genus, family=None):
        lpk = self.pk(Language, lid)

        # check whether we have to create a new genus and maybe even family:
        if family:
            if isinstance(family, (tuple, list)):
                family = self.insert(Family, id=family[0], name=family[1])
            elif isinstance(family, string_types):
                family = self.pk(Family, family)

        if isinstance(genus, (tuple, list)):
            assert family
            genus = self.insert(
                Genus, id=genus[0], name=genus[1], icon=genus[2], family_pk=family)
        elif isinstance(genus, string_types):
            genus = self.pk(Genus, genus)

        self.update(WalsLanguage, dict(genus_pk=genus), pk=lpk)

    def update_name(self, lid, newname, other=None):
        lpk = self.pk(Language, lid)
        self.update(Language, dict(name=newname), pk=lpk)
        self.update(
            WalsLanguage, dict(ascii_name=ascii_name(newname)), pk=lpk)
        if other:
            ipk = self.insert(Identifier, name=other, description='other', type='name')
            self.insert(LanguageIdentifier, identifier_pk=ipk, language_pk=lpk)

    def update_source(self, sid, **kw):
        if 'year' in kw:
            try:
                kw.setdefault('year_int', int(kw['year']))
            except ValueError:
                pass
        pk = self.pk(Source, sid)
        self.update(Source, kw, pk=pk)

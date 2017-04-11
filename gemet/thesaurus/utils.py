import re
from base64 import encodestring, decodestring
from zlib import compress, decompress

from gemet.thesaurus import PENDING, PUBLISHED, DELETED_PENDING
from gemet.thesaurus import SEARCH_FIELDS, SEARCH_SEPARATOR
from gemet.thesaurus.models import Concept, Property, Version


def is_rdf(request):
    accepts = request.META.get('HTTP_ACCEPT', '*/*')
    parts = accepts.split(',')
    return 'application/rdf+xml' in parts


def regex_search(query, language, heading):
    return (
        Property.published
        .filter(
            name='prefLabel',
            language__code=language.code,
            concept__namespace__heading=heading,
            value__iregex=r'%s' % query,
        )
        .extra(
            select={
                'value_coll': 'value COLLATE {0}'.format(language.charset),
                'name': 'value',
                'id': 'concept_id',
            },
            order_by=['value_coll']
        )
        .values('id', 'concept__code', 'name')
    )


def search_queryset(query, language, search_mode=1, heading='Concepts',
                    api_call=False, status_values=[]):
    status_values = status_values or Property.PUBLISHED_STATUS_OPTIONS
    if api_call:
        if search_mode == 4:
            values = (
                api_search(query, language, status_values, 0, heading) or
                api_search(query, language, status_values, 1, heading) or
                api_search(query, language, status_values, 2, heading) or
                api_search(query, language, status_values, 3, heading)
            )
        else:
            values = api_search(query, language, status_values, search_mode,
                                heading)
    else:
        values = insite_search(query, language, status_values, heading)

    return values


def api_search(query, language, status_values, search_mode, headings):
    search_types = {
        0: [query],
        1: [query + '%%'],
        2: ['%%' + query],
        3: ['%%' + query + '%%']
    }
    query_search = search_types.get(search_mode)

    return (
        Property.objects
        .filter(
            name='prefLabel',
            language__code=language.code,
            status__in=status_values,
            concept__namespace__heading__in=headings,
        )
        .extra(
            where=['value like convert(_utf8%s using utf8)'],
            params=query_search,
        )
        .extra(
            select={
                'value_coll': 'value COLLATE {0}'.format(language.charset),
                'name': 'value',
                'id': 'concept_id',
            },
            order_by=['value_coll']
        )
        .values('id', 'concept__code', 'name')
    )


def insite_search(query, language, status_values, heading):

    return (
        Property.objects
        .filter(
            name='searchText',
            language__code=language.code,
            status__in=status_values,
            concept__namespace__heading=heading,
        )
        .extra(
            where=['value like convert(_utf8%s using utf8)'],
            params=['%%' + query + '%%'],
        )
        .extra(
            select={
                'search_text': 'value COLLATE {0}'.format(language.charset),
                'id': 'concept_id',
            },
            order_by=['search_text']
        )
        .values('id', 'search_text', 'concept__code')
    )


def get_version_choices():
    current_identifier = Version.objects.get(is_current=True).identifier
    major, middle, minor = map(int, current_identifier.split("."))
    choices = (
        ".".join(map(str, version_parts)) for version_parts in (
            (major, middle, minor+1),
            (major, middle+1, 0),
            (major+1, 0, 0),
        )
    )
    return ((choice, choice) for choice in choices)


def exp_encrypt(exp):
    return encodestring(compress(exp))


def exp_decrypt(exp):
    return decompress(decodestring(exp))


def get_form_errors(errors):
    # errors is a dictionary with a list as value for each key;
    # the function returns the a string with all the values flattened
    return ' '.join([''.join(error) for error in errors.values()])


def get_new_code(namespace):
    codes = (
        Concept.objects
        .filter(namespace=namespace)
        .exclude(code='')
        .values_list('code', flat=True)
    )
    new_code = max(map(int, codes)) + 1
    return unicode(new_code)


def split_text_into_terms(raw_text):
    pattern = re.compile("[^a-zA-Z\d \-\\)\\(:]")
    term_list = pattern.split(raw_text)
    term_list = [term.strip(' :').lower() for term in term_list if
                 term.strip(' :').lower() != '']
    return term_list


def get_search_text(concept_id, language_code, status, version):
    search_properties = (
        Property.objects
        .filter(
            concept_id=concept_id,
            language_id=language_code,
            name__in=SEARCH_FIELDS,
            status__in=[PUBLISHED, PENDING],
        )
        .values_list('value', flat=True)
    )

    if not search_properties:
        return

    search_text = SEARCH_SEPARATOR.join(search_properties)
    search_text = SEARCH_SEPARATOR + search_text + SEARCH_SEPARATOR

    return Property(
        concept_id=concept_id,
        language_id=language_code,
        name='searchText',
        value=search_text,
        is_resource=0,
        status=status,
        version_added_id=version.id
    )


def refresh_search_text(proptype, concept_id, language_code, version=None):
    if proptype not in SEARCH_FIELDS:
        return

    version = version or Version.under_work()
    new_search = get_search_text(concept_id, language_code, PENDING, version)
    if not new_search:
        return

    search_property = (
        Property.objects
        .filter(
            concept_id=concept_id,
            language_id=language_code,
            name='searchText',
            status__in=[PUBLISHED, PENDING],
        )
        .first()
    )
    if not search_property:
        pass
    elif search_property.status == PENDING:
        search_property.delete()
    elif search_property.status == PUBLISHED:
        search_property.status = DELETED_PENDING
        search_property.save()

    new_search.save()

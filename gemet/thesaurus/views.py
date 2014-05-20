from itertools import chain
from base64 import encodestring, decodestring
from zlib import compress, decompress

from django.http import Http404
from django.shortcuts import (render, get_object_or_404, redirect,
                              render_to_response)
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from gemet.thesaurus.models import (
    Language,
    Theme,
    Namespace,
    SuperGroup,
    Term,
    Group,
    Property,
    DefinitionSource,
)
from collation_charts import unicode_character_map
from forms import SearchForm
from utils import search
from gemet.thesaurus import DEFAULT_LANGCODE, NR_CONCEPTS_ON_PAGE


class _LanguageMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.langcode = kwargs.pop("langcode")
        self.language = get_object_or_404(Language, pk=self.langcode)
        return super(_LanguageMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(_LanguageMixin, self).get_context_data(**kwargs)
        context.update({"language": self.language,
                        "languages": Language.objects.values_list('code',
                                                                  flat=True)})
        return context


class AboutView(_LanguageMixin, TemplateView):
    template_name = "about.html"


class ThemesView(_LanguageMixin, TemplateView):
    template_name = "themes.html"

    def get_context_data(self, **kwargs):
        context = super(ThemesView, self).get_context_data(**kwargs)

        themes = (
            Property.objects.filter(
                name='prefLabel',
                language__code=self.langcode,
                concept_id__in=Theme.objects.values_list('id', flat=True)
            )
            .extra(select={'name': 'value',
                           'id': 'concept_id'},
                   order_by=['name'])
            .values('id', 'name')
        )

        context.update({"themes": themes})
        return context


class GroupsView(_LanguageMixin, TemplateView):
    template_name = "groups.html"

    def get_context_data(self, **kwargs):
        context = super(GroupsView, self).get_context_data(**kwargs)

        supergroups = (
            Property.objects.filter(
                name='prefLabel',
                language__code=self.langcode,
                concept_id__in=SuperGroup.objects.values_list('id', flat=True)
            )
            .extra(select={'name': 'value',
                           'id': 'concept_id'},
                   order_by=['name'])
            .values('id', 'name')
        )

        context.update({"supergroups": supergroups})
        return context


class DefinitionSourcesView(_LanguageMixin, TemplateView):
    template_name = "definition_sources.html"

    def get_context_data(self, **kwargs):
        context = super(DefinitionSourcesView, self).get_context_data(**kwargs)

        definitions = DefinitionSource.objects.all()

        context.update({"definitions": definitions})
        return context


class AlphabetsView(_LanguageMixin, TemplateView):
    template_name = "alphabets.html"

    def get_context_data(self, **kwargs):
        context = super(AlphabetsView, self).get_context_data(**kwargs)

        letters = unicode_character_map.get(self.langcode, [])

        context.update({"letters": letters})
        return context


class SearchView(_LanguageMixin, FormView):
    template_name = "search.html"
    form_class = SearchForm

    query = ''
    concepts = []

    def get_initial(self):
        return {'langcode': self.langcode}

    def get_success_url(self):
        return reverse('search', kwargs={'langcode': self.langcode})

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)

        context.update({"query": self.query, "concepts": self.concepts})
        return context

    def form_valid(self, form):
        self.query = form.cleaned_data['query']
        self.concepts = search(self.query, self.langcode, self.language)

        return self.render_to_response(self.get_context_data(form=form))


def concept(request, concept_id, langcode):
    concept = get_object_or_404(Term, pk=concept_id)
    language = get_object_or_404(Language, pk=langcode)
    languages = [p.language.code for p in concept.properties.filter(
        name='prefLabel',
        value__isnull=False)]

    concept.translations = concept.properties.filter(
        name='prefLabel'
        ).order_by(
        'language__name'
        )

    concept.set_attributes(langcode, ['prefLabel', 'definition', 'scopeNote'])

    for parent in ['group', 'theme']:
        concept.set_parent(langcode, parent)

    concept.set_siblings(langcode, 'broader')
    concept.set_siblings(langcode, 'narrower')
    concept.set_siblings(langcode, 'related')

    concept.url = request.build_absolute_uri(
        reverse('concept_redirect', kwargs={'concept_type': 'concept',
                                            'concept_code': concept.code}))

    return render(request, 'concept.html', {
        'languages': languages,
        'language': language,
        'concept': concept,
    })


def theme(request, concept_id, langcode):
    theme = get_object_or_404(Theme, pk=concept_id)
    language = get_object_or_404(Language, pk=langcode)
    languages = [p.language.code for p in theme.properties.filter(
        name='prefLabel',
        value__isnull=False)]

    theme.translations = theme.properties.filter(
        name='prefLabel'
        ).order_by(
        'language__name'
        )

    theme.set_attributes(langcode, ['prefLabel', 'definition', 'scopeNote'])

    theme.set_siblings(langcode, 'themeMember')
    theme.url = request.build_absolute_uri(
        reverse('concept_redirect', kwargs={'concept_type': 'theme',
                                            'concept_code': theme.code}))

    return render(request, 'theme.html', {
        'languages': languages,
        'language': language,
        'theme': theme,
    })


def group(request, concept_id, langcode):
    group = get_object_or_404(Group, pk=concept_id)
    language = get_object_or_404(Language, pk=langcode)
    languages = [p.language.code for p in group.properties.filter(
        name='prefLabel',
        value__isnull=False)]

    group.translations = group.properties.filter(
        name='prefLabel'
        ).order_by(
        'language__name'
        )

    group.set_attributes(langcode, ['prefLabel', 'definition', 'scopeNote'])
    group.set_siblings(langcode, 'broader')
    group.set_siblings(langcode, 'groupMember')
    group.url = request.build_absolute_uri(
        reverse('concept_redirect', kwargs={'concept_type': 'group',
                                            'concept_code': group.code}))

    return render(request, 'group.html', {
        'languages': languages,
        'language': language,
        'group': group,
    })


def supergroup(request, concept_id, langcode):
    supergroup = get_object_or_404(SuperGroup, pk=concept_id)
    language = get_object_or_404(Language, pk=langcode)
    languages = [p.language.code for p in supergroup.properties.filter(
        name='prefLabel',
        value__isnull=False)]

    supergroup.translations = supergroup.properties.filter(
        name='prefLabel'
        ).order_by(
        'language__name'
        )

    supergroup.set_attributes(langcode,
                              ['prefLabel', 'definition', 'scopeNote'])
    supergroup.set_siblings(langcode, 'narrower')

    supergroup.url = request.build_absolute_uri(
        reverse('concept_redirect', kwargs={'concept_type': 'supergroup',
                                            'concept_code': supergroup.code}))

    return render(request, 'supergroup.html', {
        'languages': languages,
        'language': language,
        'supergroup': supergroup,
    })


def exp_encrypt(exp):
    return encodestring(compress(exp))


def exp_decrypt(exp):
    return decompress(decodestring(exp))


class RelationsView(_LanguageMixin, TemplateView):
    template_name = "relations.html"

    def dispatch(self, request, *args, **kwargs):
        self.group_id = kwargs.pop("group_id")
        return super(RelationsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        expand_text = self.request.GET.get('exp')
        if expand_text:
            expand_text = expand_text.replace(' ', '+')
            expand_text = exp_decrypt(expand_text)
            expand_list = expand_text.split('-')
        else:
            expand_list = []

        group = get_object_or_404(Group, pk=self.group_id)
        group.set_attributes(self.langcode, ['prefLabel'])

        context = super(RelationsView, self).get_context_data(**kwargs)
        context.update({
            'group_id': self.group_id,
            'group': group,
            'get_params': self.request.GET.urlencode(),
            'expand_list': expand_list,
        })
        return context


def _filter_by_letter(properties, letters, startswith=True):
    if letters:
        q_queries = [Q(value__startswith=letter) for letter in letters]
        query = q_queries.pop()
        for q_query in q_queries:
            query |= q_query
        properties = properties.filter(query) if startswith \
            else properties.exclude(query)
    return properties


def _letter_exists(all_concepts, letters):
    return _filter_by_letter(all_concepts, letters).count()


def _get_concept_params(all_concepts, request, langcode):
    languages = Language.objects.values_list('code', flat=True)
    language = get_object_or_404(Language, pk=langcode)

    try:
        letter_index = int(request.GET.get('letter', '0'))
    except ValueError:
        raise Http404

    all_letters = unicode_character_map.get(langcode, [])

    startswith = True
    if letter_index == 0:
        letters = []
    elif 0 < letter_index <= len(all_letters):
        letters = all_letters[letter_index - 1]
    elif letter_index == 99:
        letters = list(chain.from_iterable(all_letters))
        startswith = False
    else:
        raise Http404

    all_concepts = _filter_by_letter(all_concepts, letters, startswith)

    paginator = Paginator(all_concepts, NR_CONCEPTS_ON_PAGE)
    page = request.GET.get('page')
    try:
        concepts = paginator.page(page)
    except PageNotAnInteger:
        concepts = paginator.page(1)
    except EmptyPage:
        concepts = paginator.page(paginator.num_pages)

    return {
        'languages': languages,
        'language': language,
        'concepts': concepts,
        'letters':
        [(l[0], _letter_exists(all_concepts, l)) for l in all_letters],
        'letter': letter_index,
        'get_params': request.GET.urlencode()
    }


def theme_concepts(request, theme_id, langcode):
    theme = get_object_or_404(Theme, pk=theme_id)
    theme.set_attributes(langcode, ['prefLabel'])
    params = _get_concept_params(theme.get_children(langcode), request,
                                 langcode)
    params.update({'theme': theme})

    return render(request, 'theme_concepts.html', params)


def alphabetic(request, langcode):
    concepts = (
        Property.objects.filter(
            name='prefLabel',
            language__code=langcode,
        )
        .extra(select={'name': 'value',
                       'id': 'concept_id'},
               order_by=['name'])
        .values('id', 'name')
    )

    return render(request, 'alphabetic_listings.html',
                  _get_concept_params(concepts, request, langcode))


def redirect_old_urls(request, view_name):
    langcode = request.GET.get('langcode', DEFAULT_LANGCODE)
    old_new_views = {'index_html': 'themes', 'groups': 'groups'}
    view = old_new_views.get(view_name)
    if not view:
        raise Http404()
    return redirect(view, langcode=langcode)


def old_concept_redirect(request):
    langcode = request.GET.get('langcode', DEFAULT_LANGCODE)
    ns = request.GET.get('ns')
    cp = request.GET.get('cp')
    if ns and cp:
        views_map = {
            'Concepts': 'concept',
            'Themes': 'theme',
            'Groups': 'group',
            'Super groups': 'supergroup'
        }
        concept_types = {
            '1': Term,
            '2': SuperGroup,
            '3': Group,
            '4': Theme
        }
        concept_type = concept_types.get(ns)
        if concept_type:
            namespace = get_object_or_404(Namespace, id=ns)
            concept = get_object_or_404(concept_type, namespace=namespace,
                                        code=cp)
            get_object_or_404(Language, pk=langcode)
            return redirect(views_map.get(namespace.heading),
                            langcode=langcode,
                            concept_id=concept.id)
        else:
            raise Http404
    else:
        raise Http404


def concept_redirect(request, concept_type, concept_code):
    concept_types = {
        'concept': Term,
        'theme': Theme,
        'group': Group,
        'supergroup': SuperGroup
    }
    model = concept_types.get(concept_type)
    if model:
        cp = get_object_or_404(model, code=concept_code)
        return redirect(concept_type, langcode=DEFAULT_LANGCODE,
                        concept_id=cp.id)
    else:
        raise Http404


def error404(request):
    language = Language.objects.get(pk=DEFAULT_LANGCODE)
    return render(request, '404.html', {'language': language})

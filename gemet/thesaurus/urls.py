from django.conf.urls import url, include
from django.conf import settings

from gemet.thesaurus import auth_views
from gemet.thesaurus import edit_views
from gemet.thesaurus import views
from gemet.thesaurus.api import ApiView


urlpatterns = [
    # Old URLs redirect
    url(
        r'^(?P<view_name>'
        'index_html|'
        'groups|'
        'rdf|'
        'gemet-backbone\.html|'
        'gemet-backbone\.rdf|'
        'gemet-definitions\.html|'
        'gemet-groups\.html|'
        'gemet-relations\.html|'
        'gemet-skoscore\.rdf|'
        'gemetThesaurus|'
        'gemet-definitions\.rdf|'
        'gemet-groups\.rdf|'
        'inspire_themes|'
        'alphabets|'
        'about|'
        'definition_sources|'
        'changes|'
        'search|'
        'alphabetic|'
        'theme_concepts|'
        'relations|'
        'webservices'
        ')$',
        views.redirect_old_urls,
        name='redirects'
    ),
    url(r'^concept$', views.old_concept_redirect, name='old_concept_redirect'),

    # Downloads
    url(r'^2004/06/gemet-schema\.rdf/?$', views.GemetSchemaView.as_view(),
        name='gemet_schema'),
    url(r'^void\.rdf/?$', views.GemetVoidView.as_view()),
    url(r'^gemet\.rdf\.gz/?$', views.download_gemet_rdf),

    # API
    url(r'^(?P<method_name>[a-zA-Z]*)$', ApiView.as_view(), name='api_root'),

    # Translatable URLs
    url(r'^(?P<langcode>[a-zA-Z-]+)/', include([
        # Static pages
        url(r'^about/$', views.AboutView.as_view(), name='about'),
        url(r'^changes/$', views.ChangesView.as_view(), name='changes'),
        url(r'^webservices/$', views.WebServicesView.as_view(),
            name='webservices'),
        url(r'^alphabets/$', views.AlphabetsView.as_view(), name='alphabets'),



        # Search
        url(r'^search/$', views.SearchView.as_view(), name='search'),

        # List pages
        url(r'^groups/$', views.GroupsView.as_view(), name='groups'),
        url(r'^themes/$', views.ThemesView.as_view(), name='themes'),
        url(r'^inspire-themes/$', views.InspireThemesView.as_view(),
            name='inspire_themes'),
        url(r'^relations/(?P<group_code>\d+)/$', views.RelationsView.as_view(),
            name='relations'),
        url(r'^theme/(?P<theme_code>\d+)/concepts/$',
            views.ThemeConceptsView.as_view(), name='theme_concepts'),
        url(r'^alphabetic/$', views.AlphabeticView.as_view(),
            name='alphabetic'),

        # Detail pages
        url(r'^concept/(?P<code>\d+)$', views.TermView.as_view(),
            name='concept'),
        url(r'^group/(?P<code>\d+)$', views.GroupView.as_view(),
            name='group'),
        url(r'^supergroup/(?P<code>\d+)$', views.SuperGroupView.as_view(),
            name='supergroup'),
        url(r'^theme/(?P<code>\d+)$', views.ThemeView.as_view(),
            name='theme'),
        url(r'^inspire-theme/(?P<code>[a-zA-Z]+)$',
            views.InspireThemeView.as_view(), name='inspire_theme'),

        # Publish pages
        url(r'^version/release$', edit_views.ReleaseVersionView.as_view(),
            name='release_version'),
        url(r'^history_of_changes', edit_views.HistoryChangesView.as_view(),
            name='history_changes'),
        url(r'^concept/(?P<id>\d+)/sources$',
            edit_views.ConceptSourcesView.as_view(), name='concept_sources'),
        url(r'^concept/(?P<id>\d+)/changes/$',
            edit_views.ConceptChangesView.as_view(),
            name='concept_changes'),

        # Edit concept pages
        url(r'^concept/add$', edit_views.AddConceptView.as_view(),
            name='concept_add'),
        url(r'^concept/(?P<code>\d+)/edit$', edit_views.TermEditView.as_view(),
            name='concept_edit'),
        url(r'^group/(?P<code>\d+)/edit$', edit_views.GroupEditView.as_view(),
            name='group_edit'),
        url(r'^supergroup/(?P<code>\d+)/edit$',
            edit_views.SuperGroupEditView.as_view(),
            name='supergroup_edit'),
        url(r'^theme/(?P<code>\d+)/edit$', edit_views.ThemeEditView.as_view(),
            name='theme_edit'),
        url(r'^concepts/except/(?P<id>\d+)/relation/(?P<relation>[a-zA-Z]+)$',
            edit_views.UnrelatedConcepts.as_view(), name='concepts_json'),
        url(r'^definition-sources/$', views.DefinitionSourcesView.as_view(),
            name='definition_sources'),
        ])),



    url(r'^(?P<langcode>[a-zA-Z-]+)/concept/(?P<id>\d+)/edit/', include([
        url(r'^property/type/(?P<name>[a-zA-Z-]+)/edit/$',
            edit_views.EditPropertyView.as_view(), name='edit_property'),
        url(r'^property/type/(?P<name>[a-zA-Z-]+)/add$',
            edit_views.AddPropertyView.as_view(), name='add_property')
        ])),

    url(r'^property/(?P<pk>\d+)/delete/$',
        edit_views.DeletePropertyView.as_view(), name='delete_property'),

    url(r'^concept/(?P<id>\d+)/relation/foreign/add/$',
        edit_views.AddForeignRelationView.as_view(), name='add_other'),
    url(r'^relation/foreign/(?P<pk>\d+)/delete/$',
        edit_views.DeleteForeignRelationView.as_view(), name='delete_other'),
    url(r'^relation/foreign/(?P<pk>\d+)/restore/$',
        edit_views.RestoreForeignRelationView.as_view(), name='restore_other'),

    url(r'^source/(?P<source_id>\d+)/target/(?P<target_id>\d+)/'
        'relation/(?P<relation_type>[a-zA-Z-]+)/', include([
            url('add/$', edit_views.AddRelationView.as_view(),
                name='add_relation'),
            url(r'delete/$', edit_views.DeleteRelationView.as_view(),
                name='delete_relation'),
            url(r'restore/$', edit_views.RestoreRelationView.as_view(),
                name='restore_relation'),
        ])),

    # Exports
    url(r'^exports/', include([
        url(r'^gemet-backbone\.html$', views.BackboneView.as_view(),
            name='gemet-backbone.html'),
        url(r'^gemet-backbone\.rdf$', views.BackboneRDFView.as_view(),
            name='gemet-backbone.rdf'),
        url(r'^gemet-definitions.html$', views.DefinitionsView.as_view(),
            name='gemet-definitions.html'),
        url(r'^gemet-groups\.html$', views.GemetGroupsView.as_view(),
            name='gemet-groups.html'),
        url(r'^gemet-relations\.html$', views.GemetRelationsView.as_view(),
            name='gemet-relations.html'),
        url(r'^gemet-skoscore\.rdf$', views.Skoscore.as_view(),
            name='gemet-skoscore.rdf'),
        url(r'^gemetThesaurus/$', views.GemetThesaurus.as_view(),
            name='gemetThesaurus'),
        url(r'^(?P<langcode>[a-zA-Z-]+)/', include([
            url(r'^rdf$', views.DownloadView.as_view(), name='download'),
            url(r'^gemet-definitions\.rdf$',
                views.DefinitionsByLanguage.as_view(),
                name='gemet-definitions.rdf'),
            url(r'^gemet-groups\.rdf$', views.GroupsByLanguage.as_view(),
                name='gemet-groups.rdf'),
            ])),
        ])),
    url(r'^(?P<concept_type>\w+)/(?P<concept_code>\d+)$',
        views.concept_redirect,
        name='concept_redirect'),
    url(r'^auth/login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^auth/logout/$', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

from django.contrib import admin
from django.utils.html import mark_safe

from gemet.thesaurus import models


class ConceptAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('code', 'label', 'namespace', 'status', 'version_added')
    list_filter = ('version_added__identifier', 'status', 'namespace')


class ForeignRelationAdmin(admin.ModelAdmin):
    search_fields = ('code',)
    list_display = ('property_type', 'concept', 'version_added', 'status',
                    'label')
    list_filter = ('version_added__identifier', 'status')


class PropertiesAdmin(admin.ModelAdmin):
    search_fields = ('name', 'value',)
    list_display = ('name', 'value', 'concept', 'language', 'status',
                    'version_added')
    list_filter = ('version_added__identifier', 'status', 'language', 'name')


class GroupAdmin(ConceptAdmin):
    pass


class SuperGroupAdmin(ConceptAdmin):
    pass


class ThemeAdmin(ConceptAdmin):
    pass


class TermAdmin(ConceptAdmin):
    pass


class AuthorizedUserAdmin(admin.ModelAdmin):
    list_display = ('username', )


class VersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'identifier', 'publication_date', 'is_current')


class SourceAdmin(admin.ModelAdmin):
    search_fields = ('abbr', 'url',)
    list_display = ('abbr', 'title', 'url')
    list_filter = ()


class AsyncTaskAdmin(admin.ModelAdmin):
    search_fields = ()
    list_display = ('date', 'user', 'version', 'status')
    list_filter = ()


class ImportAdmin(admin.ModelAdmin):
    search_fields = ()
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'started_at', 'failed_at',
        'succeeded_at', 'logs'
    )
    list_display = (
        'id', 'spreadsheet', 'admin_status', 'created_at', 'started_at',
        'failed_at', 'succeeded_at', 'action'
    )
    list_filter = ()

    class Media:
        js = ('thesaurus/js/start_import.js',)

    def action(self, obj):
        if obj.status == 'In progress':
            return mark_safe('<span style="color: gray;">N/A</span>')
        return mark_safe(
            (
                '<input id="{}" type="button" class="default start-import" '
                'value="Run">'
            ).format(obj.pk)
        )

    action.short_description = 'Action'

    def admin_status(self, obj):
        status = obj.status
        if status == 'In progress':
            status += ' (refresh to update)'
        return status

    admin_status.short_description = 'Status'


admin.site.register(models.Namespace)
admin.site.register(models.Concept, ConceptAdmin)
admin.site.register(models.Property, PropertiesAdmin)
admin.site.register(models.Language)
admin.site.register(models.Relation)
admin.site.register(models.ForeignRelation, ForeignRelationAdmin)
admin.site.register(models.Theme, ThemeAdmin)
admin.site.register(models.Group, GroupAdmin)
admin.site.register(models.SuperGroup, SuperGroupAdmin)
admin.site.register(models.Term, ConceptAdmin)
admin.site.register(models.AuthorizedUser, AuthorizedUserAdmin)
admin.site.register(models.Version, VersionAdmin)
admin.site.register(models.DefinitionSource, SourceAdmin)

admin.site.register(models.AsyncTask, AsyncTaskAdmin)
admin.site.register(models.Import, ImportAdmin)

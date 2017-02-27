import json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.views import View
from django.urls import reverse

from gemet.thesaurus.models import Concept, ForeignRelation
from gemet.thesaurus.models import FOREIGN_RELATION_TYPES, Group, Language
from gemet.thesaurus.models import Property, PropertyType, Relation
from gemet.thesaurus.models import RELATION_TYPES, SuperGroup, Theme, Term
from gemet.thesaurus.models import Version
from gemet.thesaurus.models import EditableGroup, EditableTerm
from gemet.thesaurus.models import EditableSuperGroup
from gemet.thesaurus.forms import PropertyForm, ForeignRelationForm
from gemet.thesaurus.views import GroupView, TermView, SuperGroupView


class GroupEditView(GroupView):
    context_object_name = 'concept'
    template_name = "group_edit.html"
    model = EditableGroup


class SuperGroupEditView(SuperGroupView):
    context_object_name = 'concept'
    template_name = "supergroup_edit.html"
    model = EditableSuperGroup


class TermEditView(TermView):
    template_name = "concept_edit.html"
    model = EditableTerm


class ConceptMixin(object):

    def _set_concept_model(self, parent_type, namespace):
        if parent_type not in RELATION_TYPES:
            raise Http404
        if parent_type == 'group':
            self.model = Group
        elif parent_type == 'theme':
            self.model = Theme
        elif parent_type == 'broader' and namespace == Group.NAMESPACE:
            self.model = SuperGroup
        elif parent_type == 'narrower' and namespace == SuperGroup.NAMESPACE:
            self.model = Group
        elif parent_type in ['broader', 'narrower', 'related', 'groupMember']:
            self.model = Term

    def _get_all_concepts_by_langcode(self, langcode, concept, relation):
        return list(
            Property.objects
            .filter(
                name='prefLabel',
                language__code=langcode,
                concept__namespace__heading=self.model.NAMESPACE,
                status__in=(Property.PENDING, Property.PUBLISHED),
            )
            .exclude(
                concept_id__in=concept.source_relations.filter(
                    property_type__name=relation,
                    status__in=(Relation.PENDING, Relation.PUBLISHED),
                )
                .values_list('target_id', flat=True)
            )
            .extra(select={'name': 'value',
                           'id': 'concept_id'
                           },
                   order_by=['name'])
            .values('name', 'id').all()
        )


class JsonResponseMixin(object):

    def _get_response(self, data, status, status_code):
        response = HttpResponse(json.dumps(data),
                                content_type="application/json")
        response.status = status
        response.status_code = status_code
        return response


class EditPropertyView(JsonResponseMixin, View):

    def post(self, request, langcode, id, name):
        try:
            language = Language.objects.get(code=langcode)
            concept = Concept.objects.get(id=id)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)
        form = PropertyForm(request.POST)
        if not form.is_valid():
            data = {"message": form.errors}
            return self._get_response(data, 'error', 400)
        field = Property.objects.filter(language=langcode,
                                        concept__id=id,
                                        name=name)

        published_field = field.filter(status=Property.PUBLISHED).first()
        pending_field = field.filter(status=Property.PENDING).first()

        if pending_field:
            pending_field.value = form.cleaned_data['value']
            pending_field.save()
            field = pending_field

        else:
            is_resource = False
            if published_field:
                published_field.status = Property.DELETED_PENDING
                published_field.save()
                is_resource = published_field.is_resource

            version = Version.objects.create()
            # Todo: Remove when version is stable
            field = Property.objects.create(status=Property.PENDING,
                                            is_resource=is_resource,
                                            version_added=version,
                                            concept=concept,
                                            language=language,
                                            name=name,
                                            **form.cleaned_data)
        data = {"value": field.value}
        return self._get_response(data, 'success', 200)


class RemoveParentRelationView(JsonResponseMixin, ConceptMixin, View):

    def post(self, request, langcode, id, parent_id, rel_type):
        try:
            concept = Concept.objects.get(id=id)
            self._set_concept_model(rel_type, concept.namespace.heading)
            parent_concept = self.model.objects.get(id=parent_id)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)
        relation = Relation.objects.filter(
            source=concept, target=parent_concept,
            property_type__name=rel_type)

        published = relation.filter(status=Property.PUBLISHED).first()
        pending = relation.filter(status=Property.PENDING).first()
        if published:
            published.status = Property.DELETED_PENDING
            published.save()
        if pending:
            pending.status = Property.DELETED_PENDING
            pending.save()
        if relation:
            data = {}
            return self._get_response(data, 'success', 200)
        data = {"message": 'Object does not exist.'}
        return self._get_response(data, 'error', 400)


class AddParentRelationView(JsonResponseMixin, ConceptMixin, View):

    def get_reverse_urls(self, concept_list, langcode, id, rel_type):
        for concept in concept_list:
            url_args = {'langcode': langcode,
                        'id': id,
                        'parent_id': concept['id'],
                        'rel_type': rel_type}
            remove_rev = reverse('remove_parent', kwargs=url_args)
            add_rev = reverse('add_parent', kwargs=url_args)
            concept_code = Concept.objects.get(id=concept['id']).code
            concept_rev = reverse('concept', kwargs={
                'langcode': langcode,
                'code': concept_code})
            concept['href'] = remove_rev
            concept['href_add'] = add_rev
            concept['href_concept'] = concept_rev

    def get(self, request, langcode, id, rel_type):
        try:
            concept = Concept.objects.get(id=id)
            self._set_concept_model(rel_type, concept.namespace.heading)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)

        target_concepts = self._get_all_concepts_by_langcode(
            langcode, concept, rel_type)
        self.get_reverse_urls(target_concepts, langcode, id, rel_type)
        data = {"parents": target_concepts}
        return self._get_response(data, 'success', 200)

    def post(self, request, langcode, id, parent_id, rel_type):
        try:
            concept = Concept.objects.get(id=id)
            self._set_concept_model(rel_type, concept.namespace.heading)
            parent_concept = self.model.objects.get(id=parent_id)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)

        relations = Relation.objects.filter(
            source=concept, target=parent_concept,
            property_type__name=rel_type)
        deleted = relations.filter(status=Property.DELETED).first()
        deleted_pending = relations.filter(
            status=Property.DELETED_PENDING).first()
        if deleted:
            deleted.status = Property.PENDING
            deleted.save()
        if deleted_pending:
            deleted_pending.status = Property.PENDING
            deleted_pending.save()
        # create a new relation if there isn't one pending or published
        check_relation_status = relations.filter(status__in=[Property.PUBLISHED,
                                                             Property.PENDING])
        if not check_relation_status:
            version = Version.objects.create()
            theme_property = PropertyType.objects.get(name=rel_type)
            field = Relation(source=concept, target=parent_concept,
                             status=Property.PENDING, version_added=version,
                             property_type=theme_property)
            field.save()
        data = {}
        return self._get_response(data, 'success', 200)


class AddPropertyView(JsonResponseMixin, View):

    def post(self, request, langcode, id, name):
        try:
            language = Language.objects.get(code=langcode)
            concept = Concept.objects.get(id=id)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)

        form = PropertyForm(request.POST)
        if not form.is_valid():
            data = {"message": form.errors}
            return self._get_response(data, 'error', 400)
        prop = Property.objects.filter(status=Property.PENDING,
                                       language=language,
                                       concept=concept,
                                       name=name,
                                       value=form.cleaned_data['value'])
        if prop:
            data = {"message": 'Value must be unique.'}
            return self._get_response(data, 'error', 400)
        # TODO: Remove when version is stable
        version = Version.objects.create()
        field = Property.objects.create(status=Property.PENDING,
                                        version_added=version,
                                        language=language,
                                        concept=concept,
                                        name=name,
                                        **form.cleaned_data)
        remove_url = reverse('remove_property', kwargs={'pk': field.pk})

        data = {
            "value": field.value,
            "id": field.id,
            "status": field.status,
            "url": remove_url,
        }
        return self._get_response(data, 'success', 200)


class RemovePropertyView(JsonResponseMixin, View):

    def post(self, request, pk):
        try:
            field = Property.objects.get(pk=pk)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)
        field.status = Property.DELETED_PENDING
        field.save()
        return self._get_response({}, 'success', 200)


class AddForeignRelationView(JsonResponseMixin, ConceptMixin, View):

    def get(self, request, langcode, id):
        relation_types = [{"name": prop.name,
                           "label": prop.label,
                           "id": prop.id}
                          for prop in PropertyType.objects.all()
                          if prop.name in FOREIGN_RELATION_TYPES]
        data = {"relation_types": relation_types}
        return self._get_response(data, 'success', 200)

    def post(self, request, langcode, id):
        try:
            concept = Concept.objects.get(id=id)
            property_type = PropertyType.objects.get(id=request.POST['rel_type'])
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)
        form = ForeignRelationForm(request.POST)
        if form.is_valid():
            version = Version.objects.create()
            # todo remove version when stable
            new_relation = ForeignRelation.objects.create(
                version_added=version, property_type=property_type,
                concept=concept, **form.cleaned_data)
            url_kwargs = {'langcode': langcode,
                          'id': id,
                          'relation_id': new_relation.id}
            data = {'id': new_relation.id,
                    'remove_url': reverse('remove_other', kwargs=url_kwargs)}
            return self._get_response(data, 'success', 200)
        data = {"message": form.errors}
        return self._get_response(data, 'error', 400)


class RemoveForeignRelationView(JsonResponseMixin, View):

    def post(self, request, langcode, id, relation_id):
        try:
            foreign_relation = ForeignRelation.objects.get(id=relation_id)
        except ObjectDoesNotExist:
            data = {"message": 'Object does not exist.'}
            return self._get_response(data, 'error', 400)
        foreign_relation.status = Property.DELETED_PENDING
        foreign_relation.save()
        data = {}
        return self._get_response(data, 'success', 200)
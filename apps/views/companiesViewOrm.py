import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from apps.models.models import Companies, OrPodanieIssues, ZnizenieImaniaIssues, LikvidatorIssues, KonkurzVyrovnanieIssues, KonkurzRestrukturalizaciaActors
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
import datetime


class CompaniesViewOrm(View):
    def validate_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False

    def get(self, request):
        query_params = {}

        # getting query params and validating them - if not valid then default values
        page = int(request.GET.get('page', '1'))
        query_params['page'] = str(page) if page > 0 else '1'

        per_page = int(request.GET.get('per_page', '10'))
        query_params['per_page'] = str(per_page) if per_page > 0 else '10'

        order_by = str(request.GET.get('order_by', 'cin'))
        query_params['order_by'] = order_by if order_by in [
            'cin', 'name', 'br_section', 'address_line', 'last_update'] else 'cin'

        order_type = str(request.GET.get('order_type', 'desc')).upper()
        query_params['order_type'] = order_type if order_type == 'ASC' else 'DESC'

        query_params['query'] = str(request.GET.get('query', ''))

        last_update_gte = str(request.GET.get(
            'last_update_gte', '1000-01-01'))[0:10]
        query_params['last_update_gte'] = last_update_gte if self.validate_date(
            last_update_gte) else '1000-01-01'

        last_update_lte = str(request.GET.get(
            'last_update_lte', '3000-01-01'))[0:10]
        query_params['last_update_lte'] = last_update_lte if self.validate_date(
            last_update_lte) else '3000-01-01'

        queryset = Companies.objects.annotate(or_podanie_issues_count=Count('orpodanieissues')).annotate(znizenie_imania_issues_count=Count('znizenieimaniaissues')).annotate(likvidator_issues_count=Count('likvidatorissues')).annotate(konkurz_vyrovnanie_issues_count=Count('konkurzvyrovnanieissues')).annotate(konkurz_restrukturalizacia_actors_count=Count('konkurzrestrukturalizaciaactors')).filter(Q(name__icontains=query_params.get('query')) | Q(
            address_line__icontains=query_params.get('query'))).filter(last_update__gte=query_params.get('last_update_gte')).filter(last_update__lte=query_params.get('last_update_lte'))

        # ordering items
        if query_params.get('order_type') == 'ASC':
            queryset = queryset.order_by(
                F(query_params.get('order_by')).asc(nulls_last=True))
        else:
            queryset = queryset.order_by(
                F(query_params.get('order_by')).desc(nulls_last=True))

        # pagination
        paginator = Paginator(queryset, int(query_params.get(
            'per_page')))
        queryset_page = paginator.page(int(query_params.get('page')))

        # serialization
        response = []
        for record in queryset_page:
            data = {
                'cin': record.cin,
                'name': record.name,
                'br_section': record.br_section,
                'address_line': record.address_line,
                'last_update': record.last_update,
                'or_podanie_issues_count': record.or_podanie_issues_count,
                'znizenie_imania_issues_count': record.znizenie_imania_issues_count,
                'likvidator_issues_count': record.likvidator_issues_count,
                'konkurz_vyrovnanie_issues_count': record.konkurz_vyrovnanie_issues_count,
                'konkurz_restrukturalizacia_actors_count': record.konkurz_restrukturalizacia_actors_count
            }
            response.append(data)

        # returning json
        return JsonResponse({
            'result': [
                {'metadata': {
                    'page': int(query_params.get('page')),
                    'per_page': int(query_params.get('per_page')),
                    'pages': paginator.num_pages,
                    'total': paginator.count
                }},
                {'items': response}
            ]}, status=200)

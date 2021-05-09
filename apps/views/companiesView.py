import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.db import connection
import datetime
import math


class CompaniesView(View):
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

        query_params['query'] = '%' + str(request.GET.get('query', '')) + '%'

        last_update_gte = str(request.GET.get(
            'last_update_gte', '1000-01-01'))[0:10]
        query_params['last_update_gte'] = last_update_gte if self.validate_date(
            last_update_gte) else '1000-01-01'

        last_update_lte = str(request.GET.get(
            'last_update_lte', '3000-01-01'))[0:10]
        query_params['last_update_lte'] = last_update_lte if self.validate_date(
            last_update_lte) else '3000-01-01'

        sql_query = '''
            SELECT total_count, cin, name, br_section, address_line, last_update, 
            COALESCE(or_podanie_issues_count, 0) AS or_podanie_issues_count,
            COALESCE(znizenie_imania_issues_count, 0) AS znizenie_imania_issues_count,
            COALESCE(likvidator_issues_count, 0) AS likvidator_issues_count,
            COALESCE(konkurz_vyrovnanie_issues_count, 0) AS konkurz_vyrovnanie_issues_count,
            COALESCE(konkurz_restrukturalizacia_actors_count, 0) AS konkurz_restrukturalizacia_actors_count
            FROM (
                (
                    SELECT  COUNT(*) OVER() total_count, cin, name, br_section, address_line, last_update
                    FROM ov.companies
                ) AS companies
                LEFT JOIN
                (
                    SELECT company_id, COUNT(*) AS or_podanie_issues_count
                    FROM ov.or_podanie_issues
                    GROUP BY company_id
                ) AS or_podanie_issues
                ON companies.cin = or_podanie_issues.company_id
                LEFT JOIN
                (
                    SELECT company_id, COUNT(*) AS znizenie_imania_issues_count
                    FROM ov.znizenie_imania_issues
                    GROUP BY company_id
                ) AS znizenie_imania_issues
                ON companies.cin = znizenie_imania_issues.company_id
                LEFT JOIN
                (
                    SELECT company_id, COUNT(*) AS likvidator_issues_count
                    FROM ov.likvidator_issues
                    GROUP BY company_id
                ) AS likvidator_issues
                ON companies.cin = likvidator_issues.company_id
                LEFT JOIN
                (
                    SELECT company_id, COUNT(*) AS konkurz_vyrovnanie_issues_count
                    FROM ov.konkurz_vyrovnanie_issues
                    GROUP BY company_id
                ) AS konkurz_vyrovnanie_issues
                ON companies.cin = konkurz_vyrovnanie_issues.company_id
                LEFT JOIN
                (
                    SELECT company_id, COUNT(*) AS konkurz_restrukturalizacia_actors_count
                    FROM ov.konkurz_restrukturalizacia_actors
                    GROUP BY company_id
                ) AS konkurz_restrukturalizacia_actors
                ON companies.cin = konkurz_restrukturalizacia_actors.company_id
            ) WHERE (last_update >= '{}' AND last_update <= '{}')
            AND (name LIKE '{}'
            OR address_line LIKE '{}')
            ORDER BY {} {}
            OFFSET ({}*({}-1)) ROWS FETCH NEXT {} ROWS ONLY;
        '''.format(
            query_params.get('last_update_gte'),
            query_params.get('last_update_lte'),
            query_params.get('query'),
            query_params.get('query'),
            query_params.get('order_by'),
            query_params.get('order_type'),
            query_params.get('per_page'),
            query_params.get('page'),
            query_params.get('per_page')
        )

        # performing DB request
        with connection.cursor() as cursor:
            def dictfetchall(cursor):
                columns = [col[0] for col in cursor.description]
                return [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            cursor.execute(sql_query)
            response = dictfetchall(cursor)

        total_count = response[0].get('total_count')

        for row in response:
            del row['total_count']

        return JsonResponse({
            'result': [
                {'metadata': {
                    'page': int(query_params.get('page')),
                    'per_page': int(query_params.get('per_page')),
                    'pages': math.ceil(int(total_count)/int(query_params.get('per_page'))),
                    'total': int(total_count)
                }},
                {'items': response}
            ]}, status=200)

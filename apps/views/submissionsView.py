import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.db import connection
import datetime
import math


class SubmissionsView(View):
    def get(self, request):
        query_params = {}

        def validate_date(date_str):
            try:
                datetime.datetime.strptime(date_str, '%Y-%m-%d')
                return True
            except:
                return False

        # getting query params and validating them - if not valid then default values
        page = int(request.GET.get('page', '1'))
        query_params['page'] = str(page) if page > 0 else '1'

        per_page = int(request.GET.get('per_page', '10'))
        query_params['per_page'] = str(per_page) if per_page > 0 else '10'

        order_by = str(request.GET.get('order_by', 'id'))
        query_params['order_by'] = order_by if order_by in ['id', 'br_court_name', 'kind_name', 'cin', 'registration_date',
                                                            'corporate_body_name', 'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city'] else 'id'

        order_type = str(request.GET.get('order_type', 'desc')).upper()
        query_params['order_type'] = order_type if order_type == 'ASC' else 'DESC'

        query_params['query'] = '%' + str(request.GET.get('query', '')) + '%'

        registration_date_gte = str(request.GET.get(
            'registration_date_gte', '1000-01-01'))[0:10]
        query_params['registration_date_gte'] = registration_date_gte if validate_date(
            registration_date_gte) else '1000-01-01'

        registration_date_lte = request.GET.get(
            'registration_date_lte', '3000-01-01')
        query_params['registration_date_lte'] = registration_date_lte if validate_date(
            registration_date_lte) else '3000-01-01'

        sql_query = '''
            SELECT COUNT(*) OVER() total_count, id, br_court_name, kind_name, cin, registration_date, corporate_body_name, br_section, br_insertion, text, street, postal_code, city
            FROM ov.or_podanie_issues
            WHERE (registration_date >= '{}' AND registration_date <= '{}')
            AND (corporate_body_name LIKE '{}'
            OR city LIKE '{}'
            OR cin::text LIKE '{}')
            ORDER BY {} {}
            OFFSET ({}*({}-1)) ROWS FETCH NEXT {} ROWS ONLY;
        '''.format(
            query_params.get('registration_date_gte'),
            query_params.get('registration_date_lte'),
            query_params.get('query'),
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
            ]})

    def post(self, request):
        print('metoda pre post')

    def delete(self, request):
        print('metoda pre delete')

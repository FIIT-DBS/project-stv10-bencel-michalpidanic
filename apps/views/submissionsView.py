import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.db import connection
import json
import datetime
import math


class SubmissionsView(View):
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

        order_by = str(request.GET.get('order_by', 'id'))
        query_params['order_by'] = order_by if order_by in ['id', 'br_court_name', 'kind_name', 'cin', 'registration_date',
                                                            'corporate_body_name', 'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city'] else 'id'

        order_type = str(request.GET.get('order_type', 'desc')).upper()
        query_params['order_type'] = order_type if order_type == 'ASC' else 'DESC'

        query_params['query'] = '%' + str(request.GET.get('query', '')) + '%'

        registration_date_gte = str(request.GET.get(
            'registration_date_gte', '1000-01-01'))[0:10]
        query_params['registration_date_gte'] = registration_date_gte if self.validate_date(
            registration_date_gte) else '1000-01-01'

        registration_date_lte = request.GET.get(
            'registration_date_lte', '3000-01-01')
        query_params['registration_date_lte'] = registration_date_lte if self.validate_date(
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
        errors = []

        def add_error(field, reasons):
            errors.append(
                {
                    'field': field,
                    'reasons': reasons
                }
            )

        # getting data from request and validating them - if not valid then throw error
        br_court_name = json.loads(request.body).get('br_court_name')
        if not br_court_name:
            add_error('br_court_name', 'required')

        kind_name = json.loads(request.body).get('kind_name')
        if not kind_name:
            add_error('kind_name', 'required')

        cin = json.loads(request.body).get('cin')
        if not cin:
            add_error('cin', 'required')
        elif not cin.isnumeric():
            add_error('cin', 'not_number')

        registration_date = json.loads(request.body).get('registration_date')
        if not registration_date:
            add_error('registration_date', 'required')
        elif registration_date[:4] != str(datetime.datetime.now().year):
            add_error('registration_date', 'invalid_range')

        corporate_body_name = json.loads(
            request.body).get('corporate_body_name')
        if not corporate_body_name:
            add_error('corporate_body_name', 'required')

        br_section = json.loads(request.body).get('br_section')
        if not br_section:
            add_error('br_section', 'required')

        br_insertion = json.loads(request.body).get('br_insertion')
        if not br_insertion:
            add_error('br_insertion', 'required')

        street = json.loads(request.body).get('street')
        if not street:
            add_error('street', 'required')

        postal_code = json.loads(request.body).get('postal_code')
        if not postal_code:
            add_error('postal_code', 'required')

        city = json.loads(request.body).get('city')
        if not city:
            add_error('city', 'required')

        # return response with all errors if some exists
        if len(errors) > 0:
            return JsonResponse({'errors': errors}, status=422)

        # getting last_number in current year from ov.bulletin_issues
        with connection.cursor() as cursor:
            last_number_query = '''
                SELECT number
                FROM ov.bulletin_issues
                WHERE year = EXTRACT(YEAR FROM CURRENT_DATE)
                ORDER BY number DESC
                FETCH NEXT 1 ROWS ONLY;
            '''
            cursor.execute(last_number_query)
            last_number = cursor.fetchone()[0]
            number = last_number + 1 if last_number else 1

        # inserting new row to bulletin_issues with number and returning its id
        with connection.cursor() as cursor:
            bulletin_issues_insert = '''
                INSERT INTO ov.bulletin_issues (year, number, published_at, created_at, updated_at)
                VALUES (EXTRACT(YEAR FROM CURRENT_DATE), {}, now(), now(), now());
                SELECT currval(pg_get_serial_sequence('ov.bulletin_issues','id'));
            '''.format(number)
            cursor.execute(bulletin_issues_insert)
            bulletin_issue_id = cursor.fetchone()[0]

        # inserting new row to raw issues with bulletin_issue_id and returning its id
        with connection.cursor() as cursor:
            raw_issues_insert = '''
                INSERT INTO ov.raw_issues (bulletin_issue_id, file_name, content, created_at, updated_at)
                VALUES ({}, '-', '-', now(), now());
                SELECT currval(pg_get_serial_sequence('ov.raw_issues','id'));
            '''.format(bulletin_issue_id)
            cursor.execute(raw_issues_insert)
            raw_issue_id = cursor.fetchone()[0]

        # inserting new to or_podanie_issues with bulletin_issue_id and raw_issue_id
        with connection.cursor() as cursor:
            or_podanie_issues_insert = '''
                INSERT INTO ov.or_podanie_issues (
                    bulletin_issue_id, 
                    raw_issue_id, 
                    br_mark, 
                    br_court_code, 
                    br_court_name, 
                    kind_code, 
                    kind_name, 
                    cin, 
                    registration_date, 
                    corporate_body_name, 
                    br_section, 
                    br_insertion, 
                    text,
                    created_at,
                    updated_at,
                    address_line,
                    street, 
                    postal_code,
                    city
                )VALUES (
                    {},
                    {},
                    '-',
                    '-',
                    '{}',
                    '-',
                    '{}',
                    {},
                    '{}',
                    '{}',
                    '{}',
                    '{}',
                    '-',
                    now(),
                    now(),
                    '{}',
                    '{}',
                    '{}',
                    '{}'
                );
                SELECT * 
                FROM ov.or_podanie_issues
                WHERE id = currval(pg_get_serial_sequence('ov.or_podanie_issues', 'id'));
            '''.format(
                int(bulletin_issue_id),
                int(raw_issue_id),
                br_court_name,
                kind_name,
                int(cin),
                registration_date,
                corporate_body_name,
                br_section,
                br_insertion,
                street + ', ' + postal_code + ' ' + city,
                street,
                postal_code,
                city
            )

            def dictfetchall(cursor):
                columns = [col[0] for col in cursor.description]
                return [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            cursor.execute(or_podanie_issues_insert)
            insertion_result = dictfetchall(cursor)

        # return response with created submission
        return JsonResponse({'created_submission': insertion_result},  status=201)

    def delete(self, request, id):
        # first selecting submission with passed id and getting its raw_issue_id and bulletin_issu_id
        with connection.cursor() as cursor:
            get_ids_query = '''
                SELECT bulletin_issue_id, raw_issue_id
                FROM ov.or_podanie_issues
                WHERE id = {};
            '''.format(id)

            def dictfetchall(cursor):
                columns = [col[0] for col in cursor.description]
                return [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]

            cursor.execute(get_ids_query)
            ids = dictfetchall(cursor)

        # if not found return 404
        if not ids:
            return HttpResponse(status=404)

        # delete submission in all tables and return 204
        with connection.cursor() as cursor:
            delete_query = '''
                DELETE FROM ov.or_podanie_issues WHERE id = {};
                DELETE FROM ov.raw_issues WHERE id = {};
                DELETE FROM ov.bulletin_issues WHERE id = {};
            '''.format(id, ids[0].get('raw_issue_id'), ids[0].get('bulletin_issue_id'))

            cursor.execute(delete_query)

        return HttpResponse(status=204)

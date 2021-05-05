import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.db import connection
from apps.models.models import OrPodanieIssues
from apps.models.models import BulletinIssues
from apps.models.models import RawIssues
from django.core.paginator import Paginator
from django.db.models import Q
import datetime
import math


class SubmissionsViewOrm(View):
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
        order_by = order_by if order_by in ['id', 'br_court_name', 'kind_name', 'cin', 'registration_date',
                                            'corporate_body_name', 'br_section', 'br_insertion', 'text', 'street', 'postal_code', 'city'] else 'id'
        order_type = str(request.GET.get('order_type', 'desc')).upper()
        query_params['order_by'] = order_by if order_type == 'ASC' else str(
            '-' + order_by)

        query_params['query'] = str(request.GET.get('query', ''))

        registration_date_gte = str(request.GET.get(
            'registration_date_gte', '1000-01-01'))[0:10]
        query_params['registration_date_gte'] = registration_date_gte if self.validate_date(
            registration_date_gte) else '1000-01-01'

        registration_date_lte = request.GET.get(
            'registration_date_lte', '3000-01-01')
        query_params['registration_date_lte'] = registration_date_lte if self.validate_date(
            registration_date_lte) else '3000-01-01'

        # performing DB request
        queryset = OrPodanieIssues.objects.filter(Q(corporate_body_name__icontains=query_params.get('query')) | Q(
            city__icontains=query_params.get('query')) | Q(cin__icontains=query_params.get('query'))).filter(registration_date__gte=query_params.get('registration_date_gte')).filter(registration_date__lte=query_params.get('registration_date_lte')).order_by(query_params.get('order_by'))

        # pagination
        paginator = Paginator(queryset, int(query_params.get(
            'per_page')))
        queryset_page = paginator.page(int(query_params.get('page')))

        # serialization
        response = []
        for record in queryset_page:
            data = {
                'id': record.id,
                'br_court_name': record.br_court_name,
                'kind_name': record.kind_name,
                'cin': record.cin,
                'registration_date': record.registration_date,
                'corporate_body_name': record.corporate_body_name,
                'br_section': record.br_section,
                'br_insertion': record.br_insertion,
                'text': record.text,
                'street': record.street,
                'postal_code': record.postal_code,
                'city': record.city
            }
            response.append(data)

        return JsonResponse({
            'result': [
                {'metadata': {
                    'page': int(query_params.get('page')),
                    'per_page': int(query_params.get('per_page')),
                    'pages': paginator.num_pages,
                    'total': paginator.count
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
        br_court_name = request.POST.get('br_court_name')
        if not br_court_name:
            add_error('br_court_name', 'required')

        kind_name = request.POST.get('kind_name')
        if not kind_name:
            add_error('kind_name', 'required')

        cin = request.POST.get('cin')
        if not cin:
            add_error('cin', 'required')
        elif not cin.isnumeric():
            add_error('cin', 'not_number')

        registration_date = request.POST.get('registration_date')
        if not registration_date:
            add_error('registration_date', 'required')
        elif registration_date[:4] != str(datetime.datetime.now().year):
            add_error('registration_date', 'invalid_range')

        corporate_body_name = request.POST.get('corporate_body_name')
        if not corporate_body_name:
            add_error('corporate_body_name', 'required')

        br_section = request.POST.get('br_section')
        if not br_section:
            add_error('br_section', 'required')

        br_insertion = request.POST.get('br_insertion')
        if not br_insertion:
            add_error('br_insertion', 'required')

        street = request.POST.get('street')
        if not street:
            add_error('street', 'required')

        postal_code = request.POST.get('postal_code')
        if not postal_code:
            add_error('postal_code', 'required')

        city = request.POST.get('city')
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

    def put(self, request, id):
        print('put')

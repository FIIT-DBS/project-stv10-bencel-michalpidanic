import django
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import View
from django.db import connection
from apps.models.models import OrPodanieIssues, BulletinIssues, RawIssues
from django.core.paginator import Paginator
from django.db.models import Q, F
import json
import datetime


class SubmissionsViewOrm(View):
    def validate_date(self, date_str):
        try:
            datetime.datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False

    def get(self, request, id=''):
        if id:
            # getting object from db
            try:
                or_podanie_issues_get = OrPodanieIssues.objects.get(id=id)
            except:
                # if not found return 404
                return JsonResponse({'error': {'message': 'Záznam neexistuje'}},  status=404)

            # serialize response
            response = {
                'id': or_podanie_issues_get.id,
                'br_court_name': or_podanie_issues_get.br_court_name,
                'kind_name': or_podanie_issues_get.kind_name,
                'cin': or_podanie_issues_get.cin,
                'registration_date': or_podanie_issues_get.registration_date,
                'corporate_body_name': or_podanie_issues_get.corporate_body_name,
                'br_section': or_podanie_issues_get.br_section,
                'br_insertion': or_podanie_issues_get.br_insertion,
                'text': or_podanie_issues_get.text,
                'street': or_podanie_issues_get.street,
                'postal_code': or_podanie_issues_get.postal_code,
                'city': or_podanie_issues_get.city
            }

            # return response
            return JsonResponse({'response': response},  status=200)

        else:
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
                city__icontains=query_params.get('query')) | Q(cin__icontains=query_params.get('query'))).filter(registration_date__gte=query_params.get('registration_date_gte')).filter(registration_date__lte=query_params.get('registration_date_lte'))

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
        current_year = datetime.datetime.now().year
        last_number = BulletinIssues.objects.filter(
            year=current_year).order_by('-number').values('number')[0]
        last_number = last_number.get('number')
        number = last_number + 1 if last_number else 1

        # inserting new row to bulletin_issues with number and returning its id
        bulletin_issues_insert = BulletinIssues(year=current_year, number=int(number), published_at=datetime.datetime.now(
        ), created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        bulletin_issues_insert.save()
        bulletin_issue_id = bulletin_issues_insert.__dict__.get('id')

        # inserting new row to raw issues with bulletin_issue_id and returning its id
        raw_issues_insert = RawIssues(bulletin_issue_id=int(bulletin_issue_id), file_name='-',
                                      content='-', created_at=datetime.datetime.now(), updated_at=datetime.datetime.now())
        raw_issues_insert.save()
        raw_issue_id = raw_issues_insert.__dict__.get('id')

        # inserting new to or_podanie_issues with bulletin_issue_id and raw_issue_id
        or_podanie_issues_insert = OrPodanieIssues(bulletin_issue_id=int(bulletin_issue_id), raw_issue_id=int(raw_issue_id), br_mark='-', br_court_code='-', br_court_name=br_court_name, kind_code='-', kind_name=kind_name, cin=int(cin), registration_date=registration_date,
                                                   corporate_body_name=corporate_body_name, br_section=br_section, br_insertion=br_insertion, text='-', created_at=datetime.datetime.now(), updated_at=datetime.datetime.now(), address_line=street + ', ' + postal_code + ' ' + city, street=street, postal_code=postal_code, city=city)
        or_podanie_issues_insert.save()

        # serialize response
        response = {
            'id': or_podanie_issues_insert.id,
            'br_court_name': or_podanie_issues_insert.br_court_name,
            'kind_name': or_podanie_issues_insert.kind_name,
            'cin': or_podanie_issues_insert.cin,
            'registration_date': or_podanie_issues_insert.registration_date,
            'corporate_body_name': or_podanie_issues_insert.corporate_body_name,
            'br_section': or_podanie_issues_insert.br_section,
            'br_insertion': or_podanie_issues_insert.br_insertion,
            'text': or_podanie_issues_insert.text,
            'street': or_podanie_issues_insert.street,
            'postal_code': or_podanie_issues_insert.postal_code,
            'city': or_podanie_issues_insert.city
        }

        # return response with created submission
        return JsonResponse({'created_submission': response},  status=201)

    def delete(self, request, id):
        # first selecting submission with passed id and getting its raw_issue_id and bulletin_issu_id
        try:
            ids = OrPodanieIssues.objects.get(id=id)
        except:
            # if not found return 404
            return JsonResponse({'error': {'message': 'Záznam neexistuje'}},  status=404)

        # delete submission in all tables and return 204
        raw_issue_id = ids[0].get('raw_issue_id')
        bulletin_issue_id = ids[0].get('bulletin_issue_id')
        OrPodanieIssues.objects.filter(id=id).delete()
        RawIssues.objects.filter(id=raw_issue_id).delete()
        BulletinIssues.objects.filter(id=bulletin_issue_id).delete()

        return HttpResponse(status=204)

    def put(self, request, id):
        try:
            or_podanie_issues_object = OrPodanieIssues.objects.get(id=id)
        except:
            # if not found return 404
            return JsonResponse({'error': {'message': 'Záznam neexistuje'}},  status=404)

        errors = []

        def add_error(field, reasons):
            errors.append(
                {
                    'field': field,
                    'reasons': reasons
                }
            )

        # getting data from request and validating them - if not valid then throw error
        try:
            br_court_name = json.loads(request.body).get('br_court_name')

            kind_name = json.loads(request.body).get('kind_name')

            cin = json.loads(request.body).get('cin')
            if cin and not cin.isnumeric():
                add_error('cin', 'not_number')

            registration_date = json.loads(
                request.body).get('registration_date')
            if registration_date and registration_date[:4] != str(datetime.datetime.now().year):
                add_error('registration_date', 'invalid_range')

            corporate_body_name = json.loads(
                request.body).get('corporate_body_name')

            br_section = json.loads(request.body).get('br_section')

            br_insertion = json.loads(request.body).get('br_insertion')

            street = json.loads(request.body).get('street')

            postal_code = json.loads(request.body).get('postal_code')

            city = json.loads(request.body).get('city')
        except:
            # raise error if body is empty
            add_error('body', 'no_request_data')

        # return response with all errors if some exists
        if len(errors) > 0:
            return JsonResponse({'errors': errors}, status=422)

        # put method
        or_podanie_issues_object.br_court_name = br_court_name if br_court_name else or_podanie_issues_object.br_court_name
        or_podanie_issues_object.kind_name = kind_name if kind_name else or_podanie_issues_object.kind_name
        or_podanie_issues_object.cin = int(
            cin) if cin else or_podanie_issues_object.cin
        or_podanie_issues_object.registration_date = registration_date if registration_date else or_podanie_issues_object.registration_date
        or_podanie_issues_object.corporate_body_name = corporate_body_name if corporate_body_name else or_podanie_issues_object.corporate_body_name
        or_podanie_issues_object.br_section = br_section if br_section else or_podanie_issues_object.br_section
        or_podanie_issues_object.br_insertion = br_insertion if br_insertion else or_podanie_issues_object.br_insertion
        or_podanie_issues_object.updated_at = datetime.datetime.now()
        or_podanie_issues_object.street = street if street else or_podanie_issues_object.street
        or_podanie_issues_object.postal_code = postal_code if postal_code else or_podanie_issues_object.postal_code
        or_podanie_issues_object.city = city if city else or_podanie_issues_object.city
        or_podanie_issues_object.save()

        # serialize response
        response = {
            'id': or_podanie_issues_object.id,
            'br_court_name': or_podanie_issues_object.br_court_name,
            'kind_name': or_podanie_issues_object.kind_name,
            'cin': or_podanie_issues_object.cin,
            'registration_date': or_podanie_issues_object.registration_date,
            'corporate_body_name': or_podanie_issues_object.corporate_body_name,
            'br_section': or_podanie_issues_object.br_section,
            'br_insertion': or_podanie_issues_object.br_insertion,
            'text': or_podanie_issues_object.text,
            'street': or_podanie_issues_object.street,
            'postal_code': or_podanie_issues_object.postal_code,
            'city': or_podanie_issues_object.city
        }

        # return response with created submission
        return JsonResponse({'response': response},  status=201)

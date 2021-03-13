import django
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.db import connection
import datetime


class UptimeView():
    def getHealth(request):
        query = '''SELECT date_trunc('second', current_timestamp - pg_postmaster_start_time()) as uptime;'''
        with connection.cursor() as cursor:
            cursor.execute(query)
            delta = cursor.fetchone()

        response = ''
        for i in delta:
            response += str(i)

        return JsonResponse({'pgsql': {'uptime': response}})

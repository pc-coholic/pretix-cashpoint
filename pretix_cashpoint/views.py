import json
import logging
import string

import dateutil.parser
from django.db import transaction
from django.db.models import Count, Q
from django.http import (
    HttpResponseForbidden, HttpResponseNotFound, JsonResponse,
)
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from pretix.base.models import Checkin, Event, Order, OrderPosition
from pretix.base.models.event import SubEvent
from pretix.control.permissions import EventPermissionRequiredMixin
from pretix.helpers.urls import build_absolute_uri
from pretix.multidomain.urlreverse import (
    build_absolute_uri as event_absolute_uri,
)

from rest_framework.permissions import BasePermission
from pretix.base.models.organizer import Organizer, TeamAPIToken
from pretix.base.models.organizer import TeamAPIToken

from pretix.base.services.orders import mark_order_paid

class ApiView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, **kwargs):

        try:
            self.event = Event.objects.get(
                slug=self.kwargs['event'],
                organizer__slug=self.kwargs['organizer']
            )

        except Event.DoesNotExist:
            return HttpResponseNotFound('Unknown event')

        if ('HTTP_AUTHORIZATION' not in request.META):
            return HttpResponseForbidden('Invalid key')
        else:
            model = TeamAPIToken
            try:
                key = request.META['HTTP_AUTHORIZATION'].split('Token ')[1]
                token = model.objects.select_related('team', 'team__organizer').get(token=key)
            except model.DoesNotExist:
                return HttpResponseForbidden('Invalid key')
            except IndexError:
                return HttpResponseForbidden('Invalid key')

            if not token.active:
                return HttpResponseForbidden('Token inactive or deleted')

            if (token.team.organizer.slug != self.kwargs['organizer']):
                 return HttpResponseForbidden('Invalid key')

        self.subevent = None
        if self.event.has_subevents:
            if 'subevent' in kwargs:
                self.subevent = get_object_or_404(SubEvent, event=self.event, pk=kwargs['subevent'])
            else:
                return HttpResponseForbidden('No subevent selected.')
        else:
            if 'subevent' in kwargs:
                return HttpResponseForbidden('Subevents not enabled.')

        return super().dispatch(request, **kwargs)

class ApiCashpointView(ApiView):
    def post(self, request, **kwargs):
        logger = logging.getLogger(__name__)

        response = {}

        if 'datetime' in request.POST:
            dt = dateutil.parser.parse(request.POST.get('datetime'))
        else:
            dt = now()

        try:
            with transaction.atomic():
                order = Order.objects.get(
                    event = self.event,
                    code = self.kwargs['code'].upper(),
                )

                if order.status != Order.STATUS_PENDING:
                    response['status'] = 'error'
                    response['reason'] = order.status
                else:
                    try:
                        mark_order_paid(order, manual=True)
                    except Quota.QuotaExceededException:
                        response['status'] = 'error'
                        response['reason'] = 'quota_exceeded'

                    order.comment = order.comment + "\nOrder has been marked as paid by pretix-cashpoint."
                    order.save()
                    response['status'] = 'ok'

        except Order.DoesNotExist:
            response['status'] = 'error'
            response['reason'] = 'unknown_ticket'

        return JsonResponse(response)

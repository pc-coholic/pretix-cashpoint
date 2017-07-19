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

API_VERSION = 3
from rest_framework.permissions import BasePermission
from pretix.base.models.organizer import Organizer, TeamAPIToken
from pretix.base.models.organizer import TeamAPIToken

class ApiView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, **kwargs):
        #return super().dispatch(request, **kwargs) # !!!

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
        secret = request.POST.get('secret', '!INVALID!')
        force = request.POST.get('force', 'false') in ('true', 'True')
        nonce = request.POST.get('nonce')
        response = {
            'version': API_VERSION,
        }

        if 'datetime' in request.POST:
            dt = dateutil.parser.parse(request.POST.get('datetime'))
        else:
            dt = now()
        return JsonResponse(response) # !!!
        try:
            with transaction.atomic():
                created = False
                op = OrderPosition.objects.select_related('item', 'variation', 'order', 'addon_to').get(
                    order__event=self.event, secret=secret, subevent=self.subevent
                )
                if op.order.status == Order.STATUS_PAID or force:
                    ci, created = Checkin.objects.get_or_create(position=op, defaults={
                        'datetime': dt,
                        'nonce': nonce,
                    })
                else:
                    response['status'] = 'error'
                    response['reason'] = 'unpaid'

            if 'status' not in response:
                if created or (nonce and nonce == ci.nonce):
                    response['status'] = 'ok'
                    if created:
                        op.order.log_action('pretix.plugins.pretixdroid.scan', data={
                            'position': op.id,
                            'positionid': op.positionid,
                            'first': True,
                            'forced': op.order.status != Order.STATUS_PAID,
                            'datetime': dt,
                        })
                else:
                    if force:
                        response['status'] = 'ok'
                    else:
                        response['status'] = 'error'
                        response['reason'] = 'already_redeemed'
                    op.order.log_action('pretix.plugins.pretixdroid.scan', data={
                        'position': op.id,
                        'positionid': op.positionid,
                        'first': False,
                        'forced': force,
                        'datetime': dt,
                    })

            response['data'] = {
                'secret': op.secret,
                'order': op.order.code,
                'item': str(op.item),
                'variation': str(op.variation) if op.variation else None,
                'attendee_name': op.attendee_name or (op.addon_to.attendee_name if op.addon_to else ''),
            }

        except OrderPosition.DoesNotExist:
            response['status'] = 'error'
            response['reason'] = 'unknown_ticket'

        return JsonResponse(response)

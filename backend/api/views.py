from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError
from rest_framework.request import Request

from . import shorten
from .exceptions import Conflict


@api_view(['POST'])
def shorten_view(request: Request) -> HttpResponse:
    url = _get_url(request)
    slug = _get_slug(request)
    _shorten(slug, url)
    response = HttpResponse(slug)
    response['Content-Type'] = 'text/plain; charset=utf-8'
    return response


def _get_url(request: Request) -> str:
    try:
        return request.data['url']
    except KeyError as e:
        raise ParseError() from e


def _get_slug(request: Request) -> str:
    try:
        return request.data.get('slug', shorten.generate_unique_slug(6))
    except shorten.NoFreeSlugsError as e:
        raise Conflict('Random slug space is exhausted. Try shortening with a longer slug.') from e


def _shorten(slug: str, url: str) -> None:
    try:
        shorten.shorten(slug, url)
    except shorten.ShortenDuplicateError as e:
        raise Conflict('This slug is already occupied.') from e
    except shorten.ShortenBadInputError as e:
        raise ParseError(str(e)) from e


@api_view(['GET'])
def unshorten_view(request: Request) -> HttpResponse:
    try:
        url = shorten.unshorten(request.query_params['slug'])
    except shorten.UnshortenError:
        return HttpResponseNotFound()
    except KeyError:
        return HttpResponseBadRequest()
    return HttpResponse(url)


def redirect_view(request: HttpRequest, slug: str) -> HttpResponse:
    try:
        return redirect(shorten.unshorten(slug))
    except shorten.UnshortenError:
        return HttpResponseNotFound()


@api_view(['GET'])
def slug_view(request: Request) -> HttpResponse:
    try:
        return HttpResponse(shorten.generate_unique_slug(int(request.query_params['length'])))
    except shorten.NoFreeSlugsError:
        return HttpResponse('Random slug space is exhausted. Try shortening with a longer slug.',
                            status=409)
    except KeyError:
        return HttpResponseBadRequest('Slug length has to be specified.')
    except ValueError as e:
        return HttpResponseBadRequest(str(e))

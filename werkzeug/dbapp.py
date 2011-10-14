#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from optparse import OptionParser

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.wsgi import SharedDataMiddleware

from dblib import DbConnection
from templating import render

from film import FilmHandler


class DatabaseApp(object):
    def __init__(self, dbname):
        self.dbconn = DbConnection(dbname)
        self.film = FilmHandler(self.dbconn)
        self.url_map = Map([
                Rule('/', endpoint='index'),
                Rule('/films', endpoint='film'),
                Rule('/film/<path:parts>', endpoint='film')
                ])

    def index(self, request):
        return render('home.html')

    def error404(self, msg=''):
        return render('error/404.html', msg=str(msg))

    def dispatch(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            if endpoint == 'index':
                return getattr(self, endpoint)(request, **values)
            else:
                return self.film.dispatch(request)
        except NotFound as exc:
            response = self.error404(exc.description)
            response.status_code = 404
            return response
        except HTTPException as exc:
            return exc

    def wsgi_app(self, environ, start_response):
        req = Request(environ)
        response = self.dispatch(req)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(dbname=''):
    app = DatabaseApp(dbname)
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  os.path.join(os.path.dirname(__file__), 'static')})
    return app


if __name__ == '__main__':
    from werkzeug.serving import run_simple

    parser = OptionParser("usage: %prog [options] dbname")
    parser.add_option('-p', '--port', dest='port', type='int',
                      help="port number to listen to (default %default)")
    parser.set_defaults(port=8080)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Database name not specified")

    run_simple('127.0.0.1', options.port, create_app(args[0]),
               use_debugger=True, use_reloader=True)

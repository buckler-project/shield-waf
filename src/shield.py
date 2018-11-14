#!/usr/bin/env python
import os, sys, ssl

# get parent's path
path = os.path.dirname(os.path.abspath('__file__'))
path = path.split('/')[:-1]
path = '/'.join(path)

# change directry
os.chdir(path)
sys.path.append(path)

# run
from lib.buckler import buckler

import tornado.httpserver
import tornado.ioloop
import tornado.iostream
import tornado.web
import tornado.httpclient

from elasticsearch import Elasticsearch 


class ProxyHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        return self.recieve()

    @tornado.web.asynchronous
    def post(self):
        return self.recieve()

    def recieve(self):
        req = tornado.httpclient.HTTPRequest(
            url=self.request.uri,
            method=self.request.method,
            body=self.request.body,
            headers=self.request.headers,
            follow_redirects=False,
            allow_nonstandard_methods=True
        )

        client = tornado.httpclient.AsyncHTTPClient()
        
        suspect = f'{req.method} {req.url} HTTP/1.1\r\n{req.__dict__["_headers"]}'
        _buckler = buckler(suspect.encode())
        result = _buckler.scan()

        es = Elasticsearch()
        
        for signature, scanner in _buckler.hits().items():
            data = {
                "id" : 7,
                "date" : "2018-12-30",
                "scanner" : scanner,
                "signature" : signature,
                "signature_author" : ""
            }

            print(data)
            
            es.index(index='attack', doc_type='data', body=data)



        try:
            if result:
                raise tornado.httpclient.HTTPError(403)
            client.fetch(req, self.get_response)

        except tornado.httpclient.HTTPError as e:
            if hasattr(e, 'response') and e.response:
                get_response(e.response)
            else:
                self.set_status(500)
                self.write('500 error:\n' + str(e))
                self.finish()

    def get_response(self, response):
        if response.error and not isinstance(response.error,tornado.httpclient.HTTPError):
            self.set_status(500)
            self.write('500 error:\n' + str(response.error))
            self.finish()
        else:
            self.set_status(response.code)
            for header in ('Date', 'Cache-Control', 'Server', 'Content-Type', 'Location'):
                v = response.headers.get(header)
                if v:
                    self.set_header(header, v)
            if response.body:
                self.write(response.body)

            self.finish()

def main(port):
    app = tornado.web.Application(
        [(r'.*', ProxyHandler),]
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(port)

    print("Server is up ...")
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    port = 8000

    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    print ("Starting cache proxy on port %d" % port)
    main(port)

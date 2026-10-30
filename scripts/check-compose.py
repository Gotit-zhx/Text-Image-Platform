#!/usr/bin/env python3
"""Read-only HTTP smoke check for the Compose stack; no fixture or account writes."""
import json
import sys
from urllib.request import urlopen


def main():
    base = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
    for path in ('/', '/admin/login', '/admin/posts', '/detail/1'):
        with urlopen(base + path, timeout=15) as response:
            body = response.read().decode()
            assert response.status == 200, (path, response.status)
            assert 'text/html' in response.headers.get('Content-Type', ''), path
            assert 'id="app"' in body and '/assets/' in body, path
            assert response.headers.get('X-Content-Type-Options') == 'nosniff', path
            assert response.headers.get('Referrer-Policy') == 'no-referrer', path
        print('PASS Vue route:', path)
    with urlopen(base + '/django-admin/login/', timeout=15) as response:
        body = response.read().decode()
        assert 'csrfmiddlewaretoken' in body and 'id_username' in body
    print('PASS Django admin uses a separate route')
    with urlopen(base + '/healthz', timeout=15) as response:
        assert json.load(response) == {'status': 'ok'}
    with urlopen(base + '/api/auth/config', timeout=15) as response:
        config = json.load(response)['data']
        assert type(config['registrationEnabled']) is bool
        assert type(config['emailAvailable']) is bool
    print('PASS database health and account policy:', config)


if __name__ == '__main__':
    main()

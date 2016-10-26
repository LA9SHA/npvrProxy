from gevent import monkey; monkey.patch_all()

import time
import requests
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request, jsonify, abort

app = Flask(__name__)

# URL format: <protocol>://<username>:<password>@<hostname>:<port>, example: https://test:1234@localhost:8866
config = {
    'npvrURL': 'http://localhost:8866',
    'npvrProxyURL': 'http://localhost:5004',
    'npvrApiSid' : '',
    'npvrApiSalt' : '',
    'npvrApiMd5Pin' : '',
    'npvrApiClientKey' : '',
    'tunerCount': 2,  # number of tuners in npvr
    'npvrWeight': 300,  # subscription priority
    'chunkSize': 1024*1024  # usually you don't need to edit this
}


@app.route('/discover.json')
def discover():
    return jsonify({
        'FriendlyName': 'npvrProxy',
        'ModelNumber': 'HDHR4-2DT',
        'FirmwareName': 'hdhomerun4_dvbt',
        'TunerCount': config['tunerCount'],
        'FirmwareVersion': '20150826',
        'DeviceID': '12345678',
        'DeviceAuth': 'test1234',
        'BaseURL': '%s' % config['npvrProxyURL'],
        'LineupURL': '%s/lineup.json' % config['npvrProxyURL']
    })


@app.route('/lineup_status.json')
def status():
    return jsonify({
        'ScanInProgress': 0,
        'ScanPossible': 1,
        'Source': "Cable",
        'SourceList': ['Cable']
    })


@app.route('/lineup.json')
def lineup():
    lineup = []

    for c in _get_channels():
          c = c['channel']
          url = '%s/auto/v%s' % (config['npvrProxyURL'], c['channelNum'])

          lineup.append({'GuideNumber': str(c['channelNum']),
                         'GuideName': c['channelName'],
                         'URL': url
                         })

    return jsonify(lineup)


@app.route('/auto/<channel>')
def stream(channel):
    url = ''
    channel = channel.replace('v', '')
    duration = request.args.get('duration', default=0, type=int)

    if not duration == 0:
        duration += time.time()

    url = '%s/live?channel=%s' % (config['npvrURL'], channel)

    if not url:
        abort(404)
    else:
        req = requests.get(url, stream=True)

        def generate():
            yield ''
            for chunk in req.iter_content(chunk_size=config['chunkSize']):
                if not duration == 0 and not time.time() < duration:
                    req.close()
                    break
                yield chunk

        return Response(generate(), content_type=req.headers['content-type'], direct_passthrough=True)


def _get_channels():
    url = '%s/public/GuideService/Channels?sid=%s' % (config['npvrURL'], config['npvrApiSid'])

    try:
        r = requests.get(url)
        return r.json()['channelsJSONObject']['Channels']

    except Exception as e:
        print('An error occured: ' + repr(e))


if __name__ == '__main__':
    http = WSGIServer(('', 5004), app.wsgi_app)
    http.serve_forever()

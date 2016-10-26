from gevent import monkey; monkey.patch_all()

import time
import requests
import hashlib
import os
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request, jsonify, abort

app = Flask(__name__)

# URL format: <protocol>://<username>:<password>@<hostname>:<port>, example: https://test:1234@localhost:8866
config = {
    'npvrURL': 'http://localhost:8866',
    'npvrProxyURL': 'http://localhost:5004',
    'npvrPIN' : '',
    'npvrSID' : '',
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
        'Source': "Antenna",
        'SourceList': ['Antenna']
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
    _check_sid()
    
    try:
        url = '%s/public/GuideService/Channels?sid=%s' % (config['npvrURL'], config['npvrSID'])
        r = requests.get(url)
        return r.json()['channelsJSONObject']['Channels']

    except Exception as e:
        print('An error occured: ' + repr(e))

def _check_sid():
    if 'sid' not in config:
        if os.path.isfile('./sid.txt'):
            with open('sid.txt', 'r') as text_file:
                config['sid'] = text_file.read()
            print 'Read SID from file.'
        else:
            _get_sid()
            
    return True

def _get_sid():
    sid = ''
    salt = ''
    clientKey = ''
    
    url = '%s/public/Util/NPVR/Client/Instantiate' % config['npvrURL']
    
    try:
        j = requests.get(url).json()
        sid = j['clientKeys']['sid']
        salt = j['clientKeys']['salt']
        md5PIN = hashlib.md5(config['npvrPIN']).hexdigest()
        string = ':%s:%s' % (md5PIN, salt)
        clientKey = hashlib.md5(string).hexdigest()
        
        url = '%s/public/Util/NPVR/Client/Initialize/%s?sid=%s' %(config['npvrURL'], clientKey, sid)
        j = requests.get(url).json()
        
        if j['SIDValidation']['validated'] == True:
            config['sid'] = sid
            with open('sid.txt', 'w') as text_file:
                text_file.write(config['sid'])
            print 'Wrote SID to file.'
                
        return True
        
    except Exception as e:
        print('An error occured: ' + repr(e))
        return False
    

if __name__ == '__main__':
    http = WSGIServer(('', 5004), app.wsgi_app)
    http.serve_forever()
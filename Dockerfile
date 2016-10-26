FROM jfloff/alpine-python:2.7-onbuild

EXPOSE 5004
COPY npvrProxy.py /npvrProxy.py
CMD python /npvrProxy.py

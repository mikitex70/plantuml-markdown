ARG PYTHON_VER=3.10
FROM python:${PYTHON_VER}-alpine AS plantuml_markdown

WORKDIR /plantuml-markdown
COPY . .
ARG MARKDOWN_VER=3.4.1

RUN \
    apk update && \
    apk upgrade && \
    apk add --no-cache \
        graphviz \
        plantuml \
        font-noto-cjk \
        wget && \
    rm -rf /var/cache/apk/* && \
    sed "s/Markdown/Markdown==$MARKDOWN_VER/" requirements.txt > /tmp/requirements.txt && \
    cat test-requirements.txt >> /tmp/requirements.txt && \
    pip install -r /tmp/requirements.txt

CMD export PATH=$PWD/test:$PATH
    



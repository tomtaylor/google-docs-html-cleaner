from flask import Flask, url_for, redirect, request, render_template, session
import os
import httplib2
import io
import apiclient
from oauth2client import client
from oauth2client.contrib.flask_util import UserOAuth2
import pypandoc
import re

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['GOOGLE_OAUTH2_CLIENT_ID'] = os.environ['GOOGLE_OAUTH2_CLIENT_ID']
app.config['GOOGLE_OAUTH2_CLIENT_SECRET'] = os.environ['GOOGLE_OAUTH2_CLIENT_SECRET']

oauth2 = UserOAuth2(app)


@app.route('/')
def index():
    return render_template('form.html', user=user())


@app.route('/parse', methods=['POST'])
def parse():
    # Just look for the thing that looks most like a file_id
    m = re.search(r'[\w_-]{25,}', request.form['url'])
    if m == None:
        return render_template('form.html',
                               url=request.form['url'],
                               user=user(),
                               error="That doesn't look like a Google Docs URL")

    file_id = m.group(0)
    return redirect(url_for('convert', file_id=file_id))


@app.route('/convert/<file_id>')
@oauth2.required(scopes=["https://www.googleapis.com/auth/drive.readonly"])
def convert(file_id):
    url = "https://docs.google.com/document/d/{}".format(file_id)
    service = apiclient.discovery.build('drive', 'v3', http=oauth2.http())
    mime = 'application/vnd.oasis.opendocument.text'
    #pylint: disable=no-member
    request = service.files().export_media(fileId=file_id,
                                           mimeType=mime)

    try:
        title = service.files().get(
            fileId=file_id, fields="name").execute()['name']
        fh = io.BytesIO()
        downloader = apiclient.http.MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download {}".format(status))

        fh.seek(0)

        # Use Markdown as an intermediate format to limit the subset of HTML we
        # convert to.
        md = convert_odt_to_md(fh.read())
        html = convert_md_to_html(md)
        return render_template('form.html', url=url, document=html, title=title,
                               user=user())
    except apiclient.errors.HttpError:
        msg = "It doesn't look like you have access to this URL"
        return render_template('form.html', url=url, error=msg, user=user())
    except httplib2.HttpLib2Error:
        msg = "There was a problem connecting to the server, please try again"
        return render_template('form.html', url=url, error=msg, user=user())


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def convert_odt_to_md(odt):
    return pypandoc.convert_text(odt, 'markdown_strict', format='odt')


def convert_md_to_html(md):
    return pypandoc.convert_text(md, 'html', format='markdown_strict')


def user():
    if oauth2.has_credentials():
        return oauth2.email
    else:
        return False

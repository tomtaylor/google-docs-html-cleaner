# Google Docs HTML Cleaner

This is a little Python Flask app that takes a Google Doc URL and converts it
into nicely formatted HTML. It will authenticate the user with Google Docs,
on the first request.

To run it, you'll need to set the following environment variables:

- `SECRET_KEY`: the Flask secret key for the session signature
- `GOOGLE_OAUTH2_CLIENT_ID`: The Google API client ID
- `GOOGLE_OAUTH2_CLIENT_SECRET`: The Google API client secret

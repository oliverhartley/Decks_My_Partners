import json
import urllib.request
import urllib.parse
import time

def get_token():
    with open('/usr/local/google/home/oliverhartley/.config/gcloud/application_default_credentials.json') as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        'client_id': creds['client_id'],
        'client_secret': creds['client_secret'],
        'refresh_token': creds['refresh_token'],
        'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())['access_token']

def run_query(sql, project='concord-prod'):
    token = get_token()
    query_payload = json.dumps({
        'query': sql,
        'useLegacySql': False,
        'timeoutMs': 120000
    }).encode()
    
    bq_req = urllib.request.Request(
        f'https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries',
        data=query_payload,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(bq_req) as resp:
            res = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        raise RuntimeError(f"BigQuery HTTP {e.code} Error: {err_msg}") from e
    
    job_id = res['jobReference']['jobId']
    
    # If job not complete, poll until complete
    while not res.get('jobComplete', False):
        time.sleep(1)
        poll_req = urllib.request.Request(
            f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries/{job_id}",
            headers={'Authorization': f'Bearer {token}'}
        )
        try:
            with urllib.request.urlopen(poll_req) as resp:
                res = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode()
            raise RuntimeError(f"BigQuery Poll HTTP {e.code} Error: {err_msg}") from e
            
    # Fetch all pages
    rows = res.get('rows', [])
    page_token = res.get('pageToken')
    
    while page_token:
        poll_req = urllib.request.Request(
            f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/queries/{job_id}?pageToken={page_token}",
            headers={'Authorization': f'Bearer {token}'}
        )
        with urllib.request.urlopen(poll_req) as resp:
            page_res = json.loads(resp.read().decode())
            rows.extend(page_res.get('rows', []))
            page_token = page_res.get('pageToken')
            
    return res.get('schema', {}), rows

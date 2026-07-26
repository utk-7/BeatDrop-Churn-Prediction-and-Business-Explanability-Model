import urllib.request, json
resp = urllib.request.urlopen("https://api.github.com/repos/utk-7/BeatDrop-Churn-Prediction-and-Business-Explanability-Model/actions/runs/30184944684/jobs")
data = json.loads(resp.read())
for step in data['jobs'][0]['steps']:
    if step['conclusion'] == 'failure':
        print(step['name'], 'failed!')

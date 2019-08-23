# Super Fantasy League
## Cricket World Cup 2019
This source code is to play an online fantasy league for a closed group of friends.

It is developed using flask framework, with firestore database and hosted on google app engine.

## Deployment
### Development Environment
Deploy code and cloud function
```
gcloud app deploy ./dev.yaml --project=firstdjango-236308
gcloud functions deploy update_scores --runtime python37 --trigger-topic update_scores --set-env-vars WC_ENVIRONMENT=dev --project=firstdjango-236308
```
### Production Environment
Deploy code and cloud function
```
gcloud app deploy ./prod.yaml --project=wcsl-241605
gcloud functions deploy update_scores --runtime python37 --trigger-topic update_scores --set-env-vars WC_ENVIRONMENT=prod --project=wcsl-241605
```
### Steps for Cloud function
1. Enable google sheets api
2. Create a topic on google console called update_scores
3. Share the wc2019 to firestore-key email account
4. ``gcloud function deploy ... `` (refer above)
5. Create a job on cloud scheduler. Use frequency ``0 * * * *`` to run every hour.
### Setup project for deployment (Optional)
``gcloud config set project wcsl-241605`` - Production
``gcloud config set project firstdjango-236308`` - Development
### Setup environment variables in Windows Power Shell
```
$env:FLASK_APP="wc.py"
$env:WC_ENVIRONMENT="dev"
$env:WC_ENVIRONMENT="prod"
```
 
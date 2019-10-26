import time
from datetime import datetime
from google.cloud import pubsub_v1

from gdatabase import google_db
from gsentiment_analysis import g_sentiment_analysis
from util import setup_credentials
import json

project_id = "yhack-2019-257102"
subscription_name = "customer-posts-sub"


# Callback must be in form:
# callback(category, data, date, post_id)
class g_sub:
    def __init__(self, callback, wait_time=10):
        setup_credentials()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.callback = callback
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_name)
        self.wait_time = wait_time

    def intermediate_callback(self, message):
        print('recieved message')
        extracted_data = json.loads(message.data.decode("utf-8"))
        extracted_date = datetime.strptime(message.attributes['date'], "%m/%d/%Y, %H:%M:%S")
        extracted_post_id = message.attributes['post_id']
        if not extracted_post_id:
            extracted_post_id = None

        extracted_category = message.attributes['category']
        message.ack()

        self.callback(extracted_category, extracted_data, extracted_date, extracted_post_id)

    def get_callbacks(self):
        self.subscriber.subscribe(self.subscription_path, callback=self.intermediate_callback)
        for i in range(self.wait_time):
            time.sleep(1)


class sentiment_publisher:
    def __init__(self):
        setup_credentials()
        self.g_db = google_db()
        self.g_sa = g_sentiment_analysis()

    def callback(self, category: str, data: dict, date: datetime, post_id: str):
        if 'sentiment' not in data:
            raise KeyError('Trying to run sentiment analysis ')
        data['sentiment'] = self.g_sa.get_sentiment(data['sentiment'])
        data['timestamp'] = date
        self.g_db.store_data(data, data_id=post_id, source=category)


if __name__ == "__main__":
    sp = sentiment_publisher()

    subscriber = g_sub(sp.callback)
    subscriber.get_callbacks()

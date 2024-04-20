import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import schedule
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class NotificationSystem:
    def __init__(self):

        self.supabase_url: str = os.getenv('SUPABASE_URL')
        self.supabase_key: str = os.getenv('SUPABASE_KEY')
        self.supabase: Client = create_client(
            self.supabase_url, self.supabase_key)

        self.notifications = None

        self.chat = ChatOpenAI(api_key=OPENAI_API_KEY,
                               model="gpt-3.5-turbo-1106", temperature=0.5)
        self.whatsapp_url = os.getenv('WHATSAPP_URL')
        self.whatsapp_headers = {
            "Authorization": "Bearer " + os.getenv('WHATSAPP_ACCESSTOKEN'),
            "Content-Type": "application/json",
        }

    def tomorrow_date(self):
        self.today = datetime.now()

        self.tomorrow = self.today + timedelta(days=1)

        self.tomorrow_date = self.tomorrow.strftime('%Y-%m-%d')

        return self.tomorrow_date

    def yesterday_date(self):
        self.today = datetime.now()

        self.yesterday = self.today + timedelta(days=-1)

        self.yesterday_date = self.yesterday.strftime('%Y-%m-%d')

        return self.yesterday_date

    def get_tomorrow_events(self):
        self.date = self.tomorrow_date()
        self.tomorrow_events = self.supabase.table(
            'Event').select('*').eq('date', str(self.date)).execute().data

        return self.tomorrow_events

    def get_yesterday_events(self):
        date = self.yesterday_date()
        self.yesterday_events = self.supabase.table(
            'Event').select('*').eq('date', str(date)).execute().data

        return self.yesterday_events

    def send_notification(self):
        tomorrow_events = self.get_tomorrow_events()

        for each_message in tomorrow_events:
            if each_message['status'] != 'Completed':
                system_response = self.chat.invoke(
                    [
                        AIMessage(content='Youre a fun and friendly notification bot that sends playful event reminders. Use one smily emoji at the beginning. Using the clients first name, event details, and event desccription, you craft fun and understandable messages with a touch of humor. Your main focus is to remind them of the upcoming event and mentioning the date of event and wish them lucks creatively at the end of each message. Keep it fun, engaging, and within 7-8 lines.'),
                        HumanMessage(
                            content=each_message['name']),
                        HumanMessage(
                            content=each_message['event']),
                        HumanMessage(
                            content=each_message['description']),
                        HumanMessage(
                            content=each_message['date']),

                    ]
                )

                data = {
                    "messaging_product": "whatsapp",
                    "to": each_message['phoneNumber'],
                    "type": "text",
                    "text": {"preview_url": False, "body": system_response.content},
                }
                requests.post(
                    self.whatsapp_url, headers=self.whatsapp_headers, json=data)
                print('Tomorrow message sent successfully')

                self.supabase.table('Event').update(
                    {'status': 'Completed'}).eq('id', each_message['id']).execute()

        yesterday_events = self.get_yesterday_events()

        for each_message in yesterday_events:
            system_response = self.chat.invoke(
                [
                    AIMessage(content='Youre a fun and friendly notification bot that sends playful event follow-ups that were yesterday. Use one smily emoji at the beginning. Using the clients first name, event details, and event desccription, you craft fun and understandable messages with a touch of humor. Your main focus is to ask them of about yesterday event and encourage them to look at positive side8 at the end of each message. Keep it fun, engaging, and within 6-8 lines.'),

                    HumanMessage(
                        content=each_message['name']),
                    HumanMessage(
                        content=each_message['event']),
                    HumanMessage(
                        content=each_message['description']),
                    HumanMessage(
                        content=each_message['date']),
                ]
            )
            data = {
                "messaging_product": "whatsapp",
                "to": each_message['phoneNumber'],
                "type": "text",
                "text": {"preview_url": False, "body": system_response.content},
            }
            requests.post(
                self.whatsapp_url, headers=self.whatsapp_headers, json=data)
            print('Yesterday message sent successfully')

            exit()


def job():
    print(f'Job executed at {datetime.now().isoformat()}')
    notification = NotificationSystem()
    notification.send_notification()


if __name__ == '__main__':
    schedule.every(24).hours.do(job)
    while True:
        schedule.run_pending()
        time.sleep(10)

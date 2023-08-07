import slack

def send_slack_notification(channel, text):
    try:
        client = slack.WebClient(token=os.getenv('xoxb-4307536185414-5527133643698-dv8Moj63VDaeWbhw8gZEXRZB'))
        response = client.chat_postMessage(channel=channel, text=text)
        if response['ok']:
            print(f"Message sent successfully to {channel}")
        else:
            print(f"Failed to send message to {channel}, error: {response['error']}")
    except Exception as e:
        print(f"Exception while trying to send message to Slack: {str(e)}")

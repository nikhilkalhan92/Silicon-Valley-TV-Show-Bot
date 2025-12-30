import os
import tweepy
from dotenv import load_dotenv

def get_api():
    load_dotenv()

    ck = os.getenv("CONSUMER_KEY")
    cs = os.getenv("CONSUMER_SECRET")
    at = os.getenv("ACCESS_TOKEN")
    aS = os.getenv("ACCESS_SECRET")

    missing = [k for k, v in [
        ("CONSUMER_KEY", ck),
        ("CONSUMER_SECRET", cs),
        ("ACCESS_TOKEN", at),
        ("ACCESS_SECRET", aS),
    ] if not v]

    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    auth = tweepy.OAuth1UserHandler(ck, cs, at, aS)
    return tweepy.API(auth, wait_on_rate_limit=True)

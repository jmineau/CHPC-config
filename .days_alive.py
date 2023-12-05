import configparser
import datetime as dt
from os import path
import random


def days_alive(birth_date, include_end_date=True):
    current_date = dt.date.today()
    days = (current_date - birth_date).days

    if include_end_date:
        days += 1

    return days


def get_suffix(days):
    last_digit = days % 10
    if days % 100 in [11, 12, 13]:
        suffix = "th"
    elif last_digit == 1:
        suffix = "st"
    elif last_digit == 2:
        suffix = "nd"
    elif last_digit == 3:
        suffix = "rd"
    else:
        suffix = "th"
    return suffix


def get_random_message():
    messages = [
        "Embrace every opportunity that comes your way!",
        "Make today the best day of your life!",
        "Believe in yourself and make it happen!",
        "Find joy in the little things today.",
        "Live each day with purpose and passion!",
        "Chase your dreams and never give up!",
        "Spread positivity and make a difference today.",
        "Take risks, learn, and grow!",
        "Make every moment count and create memories.",
        "Stay focused, stay determined, and achieve greatness!",
        "Step out of your comfort zone and embrace growth.",
        "Strive for progress, not perfection.",
        "Embrace the challenges and let them fuel your success.",
        "Create your own opportunities and make them count.",
        "Celebrate your achievements, no matter how small.",
        "Stay true to yourself and follow your own path.",
        "Believe in your abilities and unleash your potential.",
        "Be the change you wish to see in the world.",
        "Trust the journey, even if you can't see the destination.",
        "Make a positive impact wherever you go."
    ]
    return random.choice(messages)


# Get birthday
config_path = path.join(path.expanduser('~'), '.custom.config')
config = configparser.ConfigParser()
config.read(config_path)

BIRTHDATE = config['user']['BIRTHDATE']
birth_date = dt.datetime.strptime(BIRTHDATE, '%Y%m%d').date()

days = days_alive(birth_date)
suffix = get_suffix(days)
message = get_random_message()

print(f"\nToday is the {days}{suffix} day you've been alive!")
print(message)

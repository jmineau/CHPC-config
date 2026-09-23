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


MESSAGES = {
    "positivity": [
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
    ],
    "stoic": [
        "Waste no more time arguing about what a good man should be. Be one. — Marcus Aurelius",
        "You have power over your mind - not outside events. Realize this, and you will find strength. — Marcus Aurelius",
        "The best revenge is to be unlike him who performed the injury. — Marcus Aurelius",
        "The happiness of your life depends upon the quality of your thoughts. — Marcus Aurelius",
        "Accept the things to which fate binds you, and love the people with whom fate brings you together, but do so with all your heart. — Marcus Aurelius",
        "We suffer more often in imagination than in reality. — Seneca",
        "As long as you live, keep learning how to live. — Seneca",
        "Luck is what happens when preparation meets opportunity. — Seneca",
        "Difficulties strengthen the mind, as labor does the body. — Seneca",
        "If a man knows not to which port he sails, no wind is favorable. — Seneca",
        "It is not that we have a short time to live, but that we waste a lot of it. — Seneca",
        "No loss should be more regrettable to us than losing time, for it’s irretrievable. — Zeno of Citium",
        "Well-being is realized by small steps, but is truly no small thing. — Zeno of Citium",
        "Man is not worried by real problems so much as by his imagined anxieties about real problems. — Epictetus",
        "First say to yourself what you would be; and then do what you have to do. — Epictetus",
        "Keep your nose to the grindstone as to what lies within your power and make peace with what does not. — Epictetus",
        "Small minded people blame others. Average people blame themselves. The wise see all blame as foolishness. — Epictetus",
        "Wealth consists not in having great possessions, but in having few wants. — Epictetus",
        "If you want to improve, be content to be thought foolish and stupid. — Epictetus",
        "Remind yourself that your task is to be a good human being. — Marcus Aurelius"
    ]
}


def get_random_message(mode="positivity"):
    messages = MESSAGES.get(mode, MESSAGES["positivity"])
    return random.choice(messages)


# Get birthday
config_path = path.join(path.expanduser('~'), '.custom.config')
config = configparser.ConfigParser()
config.read(config_path)

BIRTHDATE = config['user']['BIRTHDATE']
birth_date = dt.datetime.strptime(BIRTHDATE, '%Y%m%d').date()

# Message mode (e.g. positivity, stoic); defaults to positivity if unset
mode = config.get('messages', 'MODE', fallback='positivity')

days = days_alive(birth_date)
suffix = get_suffix(days)
message = get_random_message(mode)

print(f"\nToday is the {days}{suffix} day you've been alive!")
print(message)

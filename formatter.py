from __future__ import print_function
from __future__ import unicode_literals
import re
import timex
import datetime
import utilities
from dateutil import parser
from collections import Counter


def format_content(raw_content):
    """
    Function to process a given news story for further formatting. Calls
    a function that extract the story text minus the date and source line. Also
    splits the sentences using the ``sentence_segmenter()`` function.

    Parameters
    ----------

    raw_content: String.
                    Content of a news story as pulled from the web scraping
                    database.

    Returns
    -------

    sent_list: List.
                List of sentences.

    """
    content = _get_story(raw_content)
    split = utilities.sentence_segmenter(content)
    return split


def _get_story(story_all):
    """
    Function to extract story text without date and source line.

    Parameters
    ----------

    story_all: String.
                Content of a news story as pulled from the web scraping
                database.

    Returns
    -------

    story: String.
            Content of story with header/frontmatter removed.

    """

    if '(Reuters)' in story_all:
        story = story_all[story_all.find('(Reuters)') + 12:]
    elif '(IANS)' in story_all:
        story = story_all[story_all.find('(IANS)') + 7:]
    elif '(ANI)' in story_all:
        story = story_all[story_all.find('(ANI)') + 7:]
    elif '(Xinhua) -- ' in story_all:
        story = story_all[story_all.find('(Xinhua) -- ') + 12:]
    elif '(UPI) -- ' in story_all:
        story = story_all[story_all.find('(UPI) -- ') + 9:]
    if bool(re.search("\xe2\x80\x93", story_all[0:32])):
        try:
            story = story_all.split("\xe2\x80\x93 ", 1)[1]
        except IndexError:
            story = story_all
    else:
        story = story_all

    return story


def get_date(message, process_date):
    """
    Function to extract date from a story. First checks for a date from the RSS
    feed itself. Then tries to pull a date from the first two sentences of a
    story. Finally turns to the date that the story was added to the database.
    For the dates pulled from the story, the function checks whether the
    difference is greater than one day from the date that the pipeline is
    parsing.

    Parameters
    ----------

    message: Dictionary.
                    Record of a single result from the web scraper.

    process_date: datetime object.
                    Datetime object indicating which date the pipeline is
                    processing. Standard is date_running - 1 day.


    Returns
    -------

    date : String.
            Date string in the form YYMMDD.

    """
    date_obj = ''
    if message['date']:
        try:
            date_obj = parser.parse(message['date'])
        except TypeError:
            date_obj = ''
    else:
        date_obj = ''

    if not date_obj:
        tagged = timex.tag(message['cleaned_text'][:2])
        dates = re.findall(r'<TIMEX2>(.*?)</TIMEX2>', tagged)
        if dates:
            try:
                date_obj = parser.parse(dates[0])
                diff_check = _check_date(date_obj, process_date)
                if diff_check:
                    date_obj = ''
            except TypeError:
                date_obj = ''
        else:
            date_obj = ''

    if not date_obj:
        date_obj = message['date']

    date = '{}{:02d}{:02d}'.format(str(date_obj.year)[2:], date_obj.month,
                                   date_obj.day)

    return date


def _check_date(date_object, process_date):
    """
    Function to check the gap between the parsed date and the actual date that
    the pipeline is processing.

    Parameters
    ----------

    date_object: datetime object.
                    Date that the _get_date function suggests as a candidate
                    date.

    process_date: datetime object.
                    Datetime object indicating which date the pipeline is
                    processing. Standard is date_running - 1 day.

    Returns
    -------

    too_big: Boolean.
                Whether the gap is one day or larger.

    """
    diff = date_object - process_date
    too_big = diff > datetime.timedelta(days=0)

    return too_big


def main(message, process_date):
    """
    Main function to parse results from the web scraper to TABARI-formatted
    output.

    Parameters
    ----------

    message: Dictionary.
                    Message from the scraper queue.

    process_date: String.
                    Date for which the pipeline is running. Usually
                    current_date - 1.

    Returns
    -------

    message: Dictionary.
                   Message dictionary with content formatted.
    """


    content = message['cleaned_text']
    formatted_content = format_content(content)
    message['sent_list'] = [sent for sent in formatted_content if sent[0] != '"']

    try:
        message['date'] = get_date(message, process_date)
    except ValueError:
        now = datetime.datetime.utcnow()
        date = '{}{:02d}{:02d}'.format(str(now.year)[2:],
                                        now.month, now.day)
        message['date'] = date

    return message

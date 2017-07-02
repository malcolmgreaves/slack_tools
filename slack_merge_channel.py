"""
This script finds all channels, private channels and direct messages
that your user participates in, downloads the complete history for
those converations and writes each conversation out to seperate json files.

This user centric history gathering is nice because the official slack data exporter
only exports public channels.

PS, this only works if your slack team has a paid account which allows for unlimited history.

PPS, this use of the API is blessed by Slack.
https://get.slack.help/hc/en-us/articles/204897248
" If you want to export the contents of your own private groups and direct messages
please see our API documentation."

get your slack user token at the bottom of this page
https://api.slack.com/web

dependencies:
 pip install slacker # https://github.com/os/slacker

usage examples
 python slack_history.py --token='123token'
 python slack_history.py --token='123token' --dryRun=True
 python slack_history.py --token='123token' --skipDirectMessages
 python slack_history.py --token='123token' --skipDirectMessages --skipPrivateChannels


fetches the complete message history for a channel/group/im

pageableObject could be:
slack.channel
slack.groups
slack.im

channelId is the id of the channel/group/im you want to download history for.
"""

# MIT License

# Copyright (c) 2016 Chandler Abraham

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import argparse
import os
import time
from datetime import datetime, timedelta


import pytz
from slacker import Slacker

from slack_history import *

def resolve_time(microseconds:str) -> str:
    pst = pytz.timezone('US/Pacific')
    epoch = datetime(1970, 1, 1, tzinfo=pst)
    seven_hours_micro = int(2.52e10)
    cookie_microseconds_since_epoch = int(microseconds.replace('.','')) - seven_hours_micro
    cookie_datetime = epoch + timedelta(microseconds=cookie_microseconds_since_epoch)
    return str(cookie_datetime)


def get_userid_to_realname(slack):
    # get all users in the slack organization
    users = slack.users.list().body['members']
    userIdNameMap = {}
    for user in users:
        userIdNameMap[user['id']] = user['profile']['real_name']
    print("found {0} users ".format(len(users)))
    return userIdNameMap

def str_attachments(attachments:list) -> str:
    def str_dict(d: dict) -> str:
        s = "{\n"
        for k in d.keys():
            s += "\t'%s':'%s',\n" % (k, d[k])
        s += "}"
        return s
    s = ""
    for a in attachments:
        s += str_dict(a) + "\n"
    return s

def resolve_message(slack: Slacker, userid_to_name: dict,
                    original_channel:str, message: dict) -> str:
    name = userid_to_name[message['user']]
    content = message['text']
    time = resolve_time(message['ts'])
    core_refmt = "[%s | %s on %s]\n%s" % (original_channel, name, time, content)
    if 'attachments' in message:
        attachments_json = str_attachments(message['attachments'])
        core_refmt = "%s\nAttachments:\n%s" % (core_refmt, attachments_json)
    return core_refmt


def get_channel(slack, channel_name):
    def get_public_channel(slack, channel_name):
        channels = slack.channels.list().body['channels']
        for channel in channels:
            if channel['name'] == channel_name:
                print("getting history for public channel {0} with id {1}".format(
                    channel['name'], channel['id']))
                messages = getHistory(slack.channels, channel['id'])
                return channel['name'], channel['id'], messages
        return None

    def get_private_channel(slack, channel_name):
        groups = slack.groups.list().body['groups']
        for group in groups:
            if group['name'] == channel_name:
                print("getting history for private channel {0} with id {1}".format(
                    group['name'], group['id']))
                messages = getHistory(slack.groups, group['id'])
                return group['name'], group['id'], messages

        return None

    result = get_private_channel(slack, channel_name)
    if result is None:
        result = get_public_channel(slack, channel_name)
        if result is None:
            print("ERROR: Invalid channel: %s" % channel_name)
    return result


def sort_messages_last_to_first(messages):
    return sorted(messages, key=lambda m: int(m['ts'].replace(".","")))


def write_channel_histories_to_new(slack, userid_to_name, histories, new_channel_name):
    print("Writing %d channel histories to new channel %s" % (len(histories), new_channel_name))
    for name, id, messages in histories:
        print("Working on channel %s (id %s) with %d messages" % (name, id, len(messages)))
        resolve = lambda m: resolve_message(slack, userid_to_name, name, m)
        for i,msg in enumerate(sort_messages_last_to_first(messages)):
            try:
                slack.chat.post_message(new_channel_name, resolve(msg))
                print("...sent [%d/%d]" % (i + 1, len(messages)))
                time.sleep(1)
            except Exception as e:
                print("error, could not send message %d due to %s, skipping" % (i+1, e))

    print("Success!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='download slack history')

    parser.add_argument('--token', help="an api token for a slack user")

    parser.add_argument(
        '--new_channel',
        help="Channel to merge into.")

    parser.add_argument(
        '--previous_channels',
        default=False,
        help="Channels to merge from.")

    args = parser.parse_args()

    slack = Slacker(args.token)
    testAuth = doTestAuth(slack)
    user_map = get_userid_to_realname(slack)

    new_channel = args.new_channel
    channels_to_merge = args.previous_channels.split(",")

    print("Merging from %d channels" % len(channels_to_merge))
    for c in channels_to_merge:
        print(c)
    print("New channel for merge: %s" % new_channel)

    histories = list(filter(lambda x: x is not None,
                            [get_channel(slack, c) for c in channels_to_merge]))

    write_channel_histories_to_new(slack, user_map, histories, new_channel)


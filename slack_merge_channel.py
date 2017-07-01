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

from slacker import Slacker

def get_private_channel(slack, channel_name):
    groups = slack.groups.list().body['groups']

    for group in groups:
        if group['name'] != channel_name:
            continue

        print("getting history for private channel {0} with id {1}".format(
            group['name'], group['id']))
        messages = getHistory(slack.groups, group['id'])
        return group['name'], group['id'], messages

def write_channel_histories_to_new(slack, histories, new_channel_name):
    print("Writing %d channel histories to new channel %s" % (len(histories), new_channel_name))
    for name, id, messages in histories:
        print("Working on channel %s (id %s) with %d messages" % (name, id, len(messages)))
        post = lambda m: "[%s]: %s" % (name, m)
        for msg in messages:
            slack.chat.post_message(new_channel_name, post(msg))
    print("Success!")

# fetch all users for the channel and return a map userId -> userName


def getUserMap(slack):
    # get all users in the slack organization
    users = slack.users.list().body['members']
    userIdNameMap = {}
    for user in users:
        userIdNameMap[user['id']] = user['name']
    print("found {0} users ".format(len(users)))
    return userIdNameMap

# get basic info about the slack channel to ensure the authentication token works


def doTestAuth(slack):
    testAuth = slack.auth.test().body
    teamName = testAuth['team']
    currentUser = testAuth['user']
    print("Successfully authenticated for team {0} and user {1} ".format(teamName, currentUser))
    return testAuth

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
    userIdNameMap = getUserMap(slack)

    new_channel = args.new_channel
    channels_to_merge = args.previous_channels.split(",")
    print("Merging from %d channels" % len(channels_to_merge))
    for c in channels_to_merge:
        print(c)
    print("New channel for merge: %s" % new_channel)

    histories = filter(lambda x: x is not None,
                       [get_private_channel(slack, c) for c in channels_to_merge])

    write_channel_histories_to_new(slack, histories, new_channel)


# slack_tools
Scripts for programatically interacting with Slack.

## Setup

Do `conda env create` then `source activate slack_tools`.

## Tools
* All tools need a [legacy token](https://api.slack.com/custom-integrations/legacy-tokens) for Slack access.
* `slack_history.py`
  * Grab a Slack team's complete history, includes public and private channels and a user's DMs.
  * From [this nice person's gist](https://gist.github.com/Chandler/fb7a070f52883849de35)
* `slack_merge_channel.py`
  * Merges the history of several channels.
  * Grabs all messages from a set of public and private channels.
  * Organizes these messages from oldest to newest.
  * Posts all of them to a new channel.
  

# slack_tools
Scripts for programatically interacting with Slack.

## Setup

Do `conda env create` then `source activate slack_tools`.

## Tools
* `slack_history.py`
  * Grab a Slack team's complete history, includes public and private channels and a user's DMs.
  * From [this nice person's gist](https://gist.github.com/Chandler/fb7a070f52883849de35)
  * Needs a [legacy token](https://api.slack.com/custom-integrations/legacy-tokens) for Slack access.

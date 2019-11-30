#!/usr/bin/env python3
import pandas as pd
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChannel, PeerChat
from parsers import log
from parsers import utils, config


async def list_dialogs(client):
    result = []
    async for item in client.iter_dialogs():
        dialog = item.dialog
        if isinstance(dialog.peer, PeerUser):
            _r = await process_dialog_with_user(client, item)
            result.extend(_r)
        elif isinstance(dialog.peer, (PeerChannel, PeerChat)):
            log.debug('Dialogs in chats/channels are not supported yet')
        else:
            log.warning('Unknown dialog type %s', dialog)
    return result

async def process_dialog_with_user(client, item):
    result = []
    conversation_with_name = item.name

    # deleted account
    if conversation_with_name == '': return result

    dialog = item.dialog
    user_id = dialog.peer.user_id
    limit = config.TELEGRAM_USER_DIALOG_MESSAGES_LIMIT
    async for message in client.iter_messages(user_id, limit=limit):
        timestamp = message.date.timestamp()
        ordinal_date = message.date.toordinal()
        text = message.message
        result.append([timestamp, user_id, conversation_with_name, '', text, 'unknown', '', ordinal_date])
    return result

async def _main_loop(client):
    me = await client.get_me()
    data = await list_dialogs(client)
    log.info('Converting to DataFrame...')
    df = pd.DataFrame(data)
    df.columns = config.ALL_COLUMNS
    df['platform'] = 'telegram'
    own_name = '{} {}'.format(me.first_name, me.last_name).strip()
    df['senderName'] = own_name
    log.info('Detecting languages...')
    df['language'] = 'unknown'
    utils.export_dataframe(df, 'telegram.pkl')
    log.info('Done.')


def main():
    with TelegramClient('session_name', config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH) as client:
        client.loop.run_until_complete(_main_loop(client))

if __name__ == '__main__':
    main()

from pyrogram import Client
from pyrogram.errors import BadRequest
import os.path, os

def read_existing_idx_id(channel_id):
    ''' returns the id of the msg that holds the index for channel_id if it already exists in the file
        otherwise returns -1 '''
    if os.path.exists('./id.txt'):
        with open('id.txt', 'r') as f:
            lines = f.readlines()

        # split the lines
        for i in range(len(lines)):
            lines[i] = lines[i].split()

        print(lines)
        # parse the lines into a dictionary
        idx_dict={}

        for pair in lines:
            try:
                pair[0] = int(pair[0])
            except IndexError as e:
                print(e)
            idx_dict[pair[0]] = int(pair[1])

        if channel_id in idx_dict:
            return idx_dict[channel_id] if channel_id in idx_dict else -1

    return -1


def generate_channel_index(app, idx_chat_id, idx_msg_id):
    # for msg in app.iter_history(channel_id):
    #     print(msg.text)
    message_text = ""
    msgs = []

    index_names = {}
    for msg in app.get_history(idx_chat_id, offset_date=int(os.environ.get('OFFSET_DATE'))):
    # for msg in app.iter_history(idx_chat_id):
        if (msg.document and ('video' in msg.document.mime_type)) or msg.video:
            msgs.append(msg)

            # decide index name based on type of msg
            if msg.video:
                # if msg.caption and msg.video.file_name:
                #     index_names[msg.message_id] = msg.caption if len(msg.caption) < len(msg.video.file_name) and converteelse msg.video.file_name
                # else:
                #     index_names[msg.message_id] = msg.caption if msg.caption else msg.video.file_name
                index_names[msg.message_id] = msg.caption if msg.caption else msg.video.file_name

            elif msg.document:
                index_names[msg.message_id] = msg.document.file_name

            # convert index name to lower
            index_names[msg.message_id] = index_names[msg.message_id].lower()
            index_names[msg.message_id] = ' '.join(index_names[msg.message_id].split('.')[:5])

    # sort the msgs based on their captions
    msgs.sort(key=lambda msg: index_names[msg.message_id])

    # traverse through all the msgs and add their link and caption to the final index
    last_indexed_msg_txt = ''
    for msg in msgs:

        # omit links to different videos of the same season
        print(index_names[msg.message_id])
        if index_names[msg.message_id][:-1] == last_indexed_msg_txt[:-1]:
            continue

        # generate link for msg and add it to the final msg text
        message_text += f'''🔷<a href={msg.link}>{index_names[msg.message_id]}</a> \n'''
        last_indexed_msg_txt = index_names[msg.message_id]

    # read id of existing index in current channel from file if it exists
    idx_msg_id = read_existing_idx_id(idx_chat_id)
    print(idx_msg_id)

    if idx_msg_id == -1:
        sent_msg = app.send_message(idx_chat_id, message_text)
        idx_msg_id = sent_msg.message_id

        #write id to file
        with open('id.txt', 'w') as f:
            f.write(f'{str(idx_chat_id)} {str(idx_msg_id)}')
    else:
        # app.edit_message_text(chat_id=idx_chat_id, message_id=idx_msg_id, text=message_text, disable_web_page_preview=True)
        try:
            app.edit_message_text(chat_id=idx_chat_id, message_id=idx_msg_id, text=message_text, disable_web_page_preview=True)
        except BadRequest as e:
            print(e)
            print(message_text)

def post_index(app, channel_id, prev_idx_id):
    index_text = generate_channel_index(channel)


def main():
    app = Client(os.environ.get('CLIENT_NAME'))
    channel_id = int(os.environ.get('CHANNEL_ID'))
    idx_msg_id = -1

    with app:
        generate_channel_index(app, channel_id, idx_msg_id)
        # print(app.get_messages(channel_id, message_ids=275))

if __name__ == '__main__':
    main()

# TODO:
# figure out why is the index posted twice
# finish refactoring post_index function

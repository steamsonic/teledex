import pyrogram
from pyrogram import Client
from pyrogram.errors import BadRequest, FloodWait
import os.path, os
import time

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

def msg_txt_from_msg_list(msgs, index_names):
    result = ""
    last_indexed_name = ''
    for msg in msgs:

        # omit links to different videos of the same season
        name = index_names[msg.message_id]
        if name[:-1] == last_indexed_name[:-1]:
            continue
        elif (name[-2:].isnumeric()
            and last_indexed_name[-2:].isnumeric()
            and name[:-2] == last_indexed_name[:-2]):
            continue

        # generate link for msg and add it to the final msg text
        # result += f'''🔹<a href={msg.link}>{name}</a> \n'''
        result += f'''🔹[{name}]({msg.link})\n'''
        last_indexed_name = name

    return result

def post_sub_index(app, msgs, index_names):
    # group name is the first character of any of the msgs' index name
    firstchar = index_names[msgs[0].message_id][0]
    group_name = firstchar if firstchar.isalpha() else 'special characters or numbers'
    index = msg_txt_from_msg_list(msgs, index_names)

    result = f'\t{group_name.capitalize()}\n' + index

    try:
        msg = app.send_message(msgs[0].chat.id, result, parse_mode="md")
    except FloodWait as e:
        time.sleep(e.x)
        msg = app.send_message(msgs[0].chat.id, result, parse_mode="md")

    print(result)
    return msg.link

def post_sub_index_wrapper(app, msgs, index_names):
    size = len(msg_txt_from_msg_list(msgs, index_names))
    post_count = size//4096 + 1
    post_size = len(msgs)//post_count
    links = []
    start = 0
    end = post_size
    for i in range(post_count):
        link = post_sub_index(app, msgs[start:end], index_names)
        links.append(link)
        start = end
        end += post_size
        end = min(end, len(msgs)-1)

    print(len(msgs), post_count)
    return(links[0])

def get_msg_list(app, idx_chat_id):
    msgs = []
    if os.path.exists('./data.txt'):
        with open('data.txt', 'r') as f:
            msgs_repr = f.readlines()
            for line in msgs_repr:
                msgs.append(eval(line))
            print("no need for tele. we got the messages already")
    else:
        msgs_repr_lines = []
        # for msg in app.get_history(idx_chat_id, offset_date=int(os.environ.get('OFFSET_DATE'))):
        for msg in app.iter_history(idx_chat_id):
            msgs.append(msg)
            msgs_repr_lines.append(repr(msg) + '\n')

        # now write the msgs to file
        with open('data.txt', 'w') as f:
            f.writelines(msgs_repr_lines)

    return msgs


def generate_channel_index(app, idx_chat_id, idx_msg_id):
    # for msg in app.iter_history(channel_id):
    #     print(msg.text)
    master_index = 'Master Index \n\n'
    msgs = []
    all_msgs = get_msg_list(app, idx_chat_id)

    index_names = {}
    # for msg in app.get_history(idx_chat_id, offset_date=int(os.environ.get('OFFSET_DATE'))):
    for msg in all_msgs:
        if (msg.document and ('video' in msg.document.mime_type)) or msg.video:
            msgs.append(msg)

            # decide index name based on type of msg
            if msg.video:
                index_names[msg.message_id] = msg.caption if msg.caption else msg.video.file_name
            elif msg.document:
                index_names[msg.message_id] = msg.document.file_name

            # convert index name to lower
            index_names[msg.message_id] = index_names[msg.message_id].lower()
            index_names[msg.message_id] = ' '.join((index_names[msg.message_id].split('.'))[:5])

    # sort the msgs based on their captions
    msgs.sort(key=lambda msg: index_names[msg.message_id])

    # break the msgs list into subgroups
    start = 0
    end = -1
    for i in range(len(msgs)-1):
        first_char = index_names[msgs[i].message_id][0]
        next_first_char = index_names[msgs[i+1].message_id][0]
        if (first_char == next_first_char) or ((not first_char.isalpha()) and (not next_first_char.isalpha())):
            continue
        end = i+1
        group_name = first_char if first_char.isalpha() else 'special characters or numbers'
        link = post_sub_index_wrapper(app, msgs[start:end], index_names)
        start = end
        master_index += f'🔹<a href={link}>index of movies starting with {group_name.capitalize()}</a>\n'
    else:
        link = post_sub_index_wrapper(app, msgs[start:], index_names)
        master_index += f'🔹<a href={link}>index of movies starting with {group_name.capitalize()}</a>\n'


    # generate the final index message
    print(master_index)

    # read id of existing index in current channel from file if it exists
    idx_msg_id = read_existing_idx_id(idx_chat_id)

    # this part of the code actually sends the messages
    if idx_msg_id == -1:
        sent_msg = app.send_message(idx_chat_id, master_index)
        idx_msg_id = sent_msg.message_id

        #write id to file
        with open('id.txt', 'w') as f:
            f.write(f'{str(idx_chat_id)} {str(idx_msg_id)}')
    else:
        # app.edit_message_text(chat_id=idx_chat_id, message_id=idx_msg_id, text=master_index, disable_web_page_preview=True)
        try:
            app.edit_message_text(chat_id=idx_chat_id, message_id=idx_msg_id, text=master_index, disable_web_page_preview=True)
        except BadRequest as e:
            print(e)
            # print(message_text)

def update_index(app, channel_id, prev_idx_id):
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

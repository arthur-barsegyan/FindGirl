# -*- coding: utf-8 -*-
import threading
import httplib
import urllib
import json

import vk
from time import sleep

from vk.exceptions import VkAPIError

group_name = 'lovensu'
COOKIE = ''
samples = 'Zebrahead'

possible_matches = []
matches_tracks = []

lock = threading.Lock()


def find_tracks(user, playlist):
    user_id = user.get('uid')

    counter = 0
    matches = 0
    while counter < len(playlist):
        if playlist[counter][4].encode('UTF-8').find(samples) != -1:
            with lock:
                matches_tracks.append([user_id, user, playlist[counter][3]])

            matches += 1
            print(playlist[counter][3])

        counter += 1

    if (matches > 0):
        with lock:
            possible_matches.append([user, matches])


def get_user_playlist(user_id):
    post_date = {
        'al': 1,
        'act': 'load_section',
        'owner_id': user_id,
        'type': 'playlist',
        'playlist_id': '-1',
        'offset': 0
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': 0,
        'Cookie': COOKIE,
        'User-Agent': USER_AGENT
    }

    playlist = []
    offset = 0
    hasMore = 1
    while hasMore:
        post_date['offset'] = offset
        body = urllib.urlencode(post_date)
        headers['Content-Length'] = len(body)

        connection = httplib.HTTPSConnection('vk.com')
        connection.request('POST', '/al_audio.php', body, headers)
        response = connection.getresponse()

        if response.status != 200:
            print '[get_user_playlist] Get bad status response: ' + str(response.status)

        response_size = response.getheader('Content-Length')
        response_body = response.read(response_size)

        data = response_body.decode('cp1251')
        split_data = data.split(u'<!>')
        raw_json = split_data[5][7:]

        json_playlist = json.loads(raw_json)

        hasMore = json_playlist['hasMore']
        offset = json_playlist['nextOffset']

        playlist.extend(json_playlist['list'])

    return playlist


def user_input():
    sleep(3)
    while 1:
        command = raw_input('Enter command: ')
        if command == 'print':
            print(possible_matches)
            print(matches_tracks)

        if command == 'exit':
            exit(0)


def write_results():
    # group_name + '_' + samples + '.txt'
    with open(('girls.txt').encode("UTF-8"), 'w') as result_file:
        counter = 0
        sort_matches = sorted(possible_matches, key=lambda match_count: possible_matches[1])

        for user in sort_matches:
            result_file.write((str(counter) + '. ' + user[0]['first_name'] + ' ' + user[0]['last_name'] + ' [id' + str(user[0]['uid']) + ']\n').encode('UTF-8'))

            i = 0
            for match in matches_tracks:
                if match[0] == user[0]['uid']:
                    result_file.write((match[2] + '\n').encode('UTF-8'))

            result_file.write('\n')
            counter += 1


def search():
    session = vk.AuthSession(app_id=6290034, user_login="{user_name}", user_password="{user_password}",
                             scope='friends,offline')
    vk_api = vk.API(session)
    # user = vk_api.users.get(user_id=22677215)

    woman_sex = 1
    man_sex = 2

    # VK Error numbers
    many_requests = 6
    user_deactivated = 15

    cur_offset = 0
    members_count = 1

    first_iter = 1
    print 'Start parsing group: ' + group_name
    while cur_offset < members_count:
        try:
            users_list = vk_api.groups.getMembers(group_id=group_name, offset=cur_offset, count=1000,
                                                  fields='sex,bdate')

            if first_iter == 1:
                members_count = users_list['count']
                print '[' + str(members_count) + ' members]'
                first_iter = 0
        except VkAPIError as e:
            print(e)
            sleep(0.5)
            continue

        print('New stage from ' + str(cur_offset) + ' to ' + str(cur_offset + 1000))
        cur_offset += 1000

        for user in users_list.get('users'):
            if user.get('sex') == woman_sex:
                try:
                    playlist = get_user_playlist(user.get('uid'))
                    find_tracks(user, playlist)
                except ValueError as e:
                    # User have private playlist :(
                    continue

        write_results()
    
    write_results()
    print('Search was done...')


def main():
    search_thread = threading.Thread(target=search, args=[])
    search_thread.start()


if __name__ == "__main__":
    main()
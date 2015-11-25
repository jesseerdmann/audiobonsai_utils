__author__ = 'Jesse'

import argparse
import collections
import datetime
import django
import os
import random
import re
import spotipy
import spotipy.util as sputil
import urllib2

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audiobonsai.settings")
#from django.conf import settings
#from rootball.models import FreshCuts
django.setup()

parser = argparse.ArgumentParser(description='load a Fresh Cuts playlist')
parser.add_argument('-pubdate', action='store', dest='pubdate', help='The date of the FreshCuts list publication')

stats_dict = {}

def getSpotifyConn(username='AudioBonsai', scope='user-read-private playlist-modify-private playlist-read-private playlist-modify-public'):
    '''
    getSpotifyConn -- connect to spotify
    '''
    token = sputil.prompt_for_user_token(username, scope)
    sp = spotipy.Spotify(auth=token)
    return sp

def buildArtistDict(album_tracks):
    artist_dict = {}
    track_dict = {}
    return_dict = {}
    duration_list = []
    #Get full track details including popularity
    uris = [x[u'uri'] for x in album_tracks]
    track_dets = sp.tracks(uris)
    #print('Track details list below:')
    #print(track_dets)

    # Identify all the artists on the album to look for singles and dictify the tracks
    for album_track in track_dets[u'tracks']:
        #print('track_dets:')
        #print(album_track)
        popularity = int(album_track[u'popularity'])
        duration = int(album_track[u'duration_ms'])
        disc_number = int(album_track[u'disc_number'])
        track_number = int(album_track[u'track_number'])
        if disc_number not in stats_dict.keys():
            stats_dict[disc_number] = {}
        if track_number not in stats_dict[disc_number]:
            stats_dict[disc_number][track_number] = {}
        if popularity not in stats_dict[disc_number][track_number]:
            stats_dict[disc_number][track_number][popularity] = 1
        else:
            stats_dict[disc_number][track_number][popularity] += 1
        if duration <= 60000:
            continue
        #if popularity not in track_dict.keys():
        #    track_dict[popularity] = {}
        #if duration not in track_dict[popularity].keys():
        #    track_dict[popularity][duration] = {}
        if duration not in track_dict.keys():
            track_dict[duration] = {}

        #track_dict[popularity][duration][album_track[u'name']] = album_track[u'uri']
        track_dict[duration][album_track[u'name']] = album_track[u'uri']
        return_dict[album_track[u'name']] = {}
        return_dict[album_track[u'name']]['uri'] = album_track[u'uri']
        return_dict[album_track[u'name']]['disc_number'] = disc_number
        return_dict[album_track[u'name']]['track_number'] = track_number

        for artist in album_track[u'artists']:
            #artist_dict[artist[u'name']] = artist[u'uri']
            if artist[u'uri'] in artist_dict.keys():
                artist_dict[artist[u'uri']]['tracks'] += 1
            else:
                artist_full = sp.artist(artist[u'uri'])
                artist_dict[artist[u'uri']] = {}
                artist_dict[artist[u'uri']]['tracks'] = 1
                artist_dict[artist[u'uri']]['name'] = artist[u'name']
                artist_dict[artist[u'uri']]['popularity'] = '-'
                if artist_full[u'popularity'] != '-':
                    artist_dict[artist[u'uri']]['popularity'] = int(artist_full[u'popularity'])
    #sorted_pops = sorted(track_dict.keys(), reverse=True)
    #if sorted_pops == None or len(sorted_pops) <= 0:
    #    return [None, None, None, None, None, None]
    #top_pop = sorted_pops[0]
    #durations = sorted(track_dict[top_pop].keys())
    #duration = durations[len(durations)/2]
    #song_names = track_dict[top_pop][duration].keys()
    #song_name = random.sample(song_names, 1)
    #selected_track = track_dict[top_pop][duration][song_name[0]]
    durations = sorted(track_dict.keys())
    duration = durations[len(durations)/2]
    song_names = track_dict[duration].keys()
    song_name = random.sample(song_names, 1)
    selected_track = track_dict[duration][song_name[0]]
    return [selected_track, return_dict, artist_dict,
            return_dict[song_name[0]]['disc_number'],
            return_dict[song_name[0]]['track_number'], song_name[0]]

def buildSinglesList(track_dict, artist_dict, max_tracks, sp, album_uri):
    selected_single = None
    selected_single_disc_number = None
    selected_single_track_number = None
    selected_single_track_name = None
    top_pop = -1
    release_date = datetime.datetime.strptime('2015-1-1', '%Y-%m-%d')

    # See if any of the artists singles are on the album
    for artist_uri in artist_dict.keys():
        if artist_dict[artist_uri]['tracks'] < max_tracks:
            continue

        #print('{0} - {1}'.format(artist_uri, artist_tracks_count))
        artist_tracks = sp.artist_albums(artist_uri, album_type='single', country='US')
        uris = [x[u'uri'] for x in artist_tracks[u'items']]
        if len(uris) == 0:
            return [selected_single, selected_single_disc_number, selected_single_track_number, selected_single_track_name]
        singles_dets = sp.albums(uris)
        #print(singles_dets)
        for artist_single in singles_dets[u'albums']:
            if artist_single[u'uri'] == album_uri:
                continue
            #print('single_dets:')
            #print(artist_single)
            song_names = [x[u'name'] for x in artist_single[u'tracks'][u'items']]
            match_name = ''
            if artist_single[u'name'] in track_dict.keys():
                match_name = artist_single[u'name']
            elif song_names[0] in track_dict.keys():
                match_name = song_names[0]
            else:
                continue
            single_release_date = datetime.datetime.strptime('1970-1-1', '%Y-%m-%d')
            try:
                single_release_date = datetime.datetime.strptime(artist_single[u'release_date'], '%Y-%m-%d')
            except:
                print('Bad date format: ' + album_dets[u'release_date'])
            #if int(artist_single[u'popularity']) >= top_pop and single_release_date > release_date:
            #print('{0} - {1} compared to {2}'.format(match_name, single_release_date, release_date))
            if single_release_date > release_date:
                selected_single = track_dict[match_name]['uri']
                selected_single_disc_number = track_dict[match_name]['disc_number']
                selected_single_track_number = track_dict[match_name]['track_number']
                selected_single_track_name = match_name
                release_date = single_release_date
    return [selected_single, selected_single_disc_number, selected_single_track_number, selected_single_track_name]

def processAlbumDets(album_dets, sp, album_count):
    #print(album_dets)
    # Get all the tracks on the album
    album_tracks = album_dets[u'tracks'][u'items']
    album_name = album_dets[u'name']
    artist_names = []
    [selected_track, track_dict, artist_dict, disc_number, track_number, track_name] = buildArtistDict(album_tracks)
    if selected_track == None:
        return [False, None, None, None, None, None]
    max_tracks = -1
    max_pop = -1
    for artist in artist_dict.keys():
        if artist_dict[artist]['tracks'] > max_tracks:
            max_tracks = artist_dict[artist]['tracks']
    for artist in artist_dict.keys():
        if artist_dict[artist]['tracks'] < max_tracks:
            continue
        if artist_dict[artist]['popularity'] > max_pop:
            max_pop = artist_dict[artist]['popularity']
    for artist in artist_dict.keys():
        if artist_dict[artist]['tracks'] == max_tracks:
            artist_names.append(artist_dict[artist]['name'])
    [selected_single, single_disc_number, single_track_number, single_name] = buildSinglesList(track_dict, artist_dict, max_tracks, sp, album_dets[u'uri'])

    # Keep the most recent single on the album, or all tracks if no single found
    if selected_single is not None:
        print(u'{6}: {0} from {1} by {2}({5}) on disc {3} as track {4}, most recent single'.format(single_name, album_name,
                                                                                        u', '.join(artist_names),
                                                                                        single_disc_number,
                                                                                        single_track_number, max_pop, album_count))
        return [True, selected_single, disc_number, track_number, max_pop, single_name]
    else:
        print(u'{6}: {0} from {1} by {2}({5}) on disc {3} as track {4}'.format(track_name, album_name, u', '.join(artist_names),
                                                                    disc_number, track_number, max_pop, album_count))
        return [False, selected_track, disc_number, track_number, max_pop, track_name]

def getAlbumsFromNewReleases(sp):
    uris = []
    rescount = 500
    limit = 50
    offset = 0
    # Get all new releases
    while(rescount > offset):
        results = sp.new_releases(country='US', limit=limit, offset=offset)
        if results == None:
            break
        #print(results)
        # Set the maximum number of releases possible
        rescount = results[u'albums'][u'total']
        uris += [x[u'uri'] for x in results[u'albums'][u'items']]
        offset = len(uris)

    return uris

def getAlbumsFromSortingHat():
    response = urllib2.urlopen('http://everynoise.com/spotify_new_releases.html')
    html = response.read()
    track_dict = {}
    artist_ranks = {}
    #print(len(html))
    track_items = html.split('</div><div class=')
    #print(len(track_items))
    group_string = re.compile(' title="artist rank: ([0-9,-]+)"><a onclick=.* href="(spotify:album:.*)">.*</i></a> <span class=trackcount>([0-9]+)</span>')
    match_string = re.compile(' title="artist rank:.*')

    for track in track_items:
        for match in match_string.findall(track):
            #print(match)
            bits = group_string.match(match)
            if bits == None:
                continue
            if int(bits.group(3)) > 2:
                track_dict[bits.group(2)] = bits.group(1)
                if bits.group(1) == '-':
                    if '-' in artist_ranks.keys():
                        artist_ranks['-'] += 1
                    else:
                        artist_ranks['-'] = 1
                elif int(bits.group(1))/1000 in artist_ranks.keys():
                    artist_ranks[int(bits.group(1))/1000] += 1
                else:
                    artist_ranks[int(bits.group(1))/1000] = 1
                #print('uri: {0}, tracks: {1}, artist rank: {2}'.format(bits.group(2), bits.group(3), bits.group(1)))

    print(len(track_dict.keys()))
    for rank in sorted(artist_ranks.keys()):
        print('{0} : {1}'.format(rank*1000, artist_ranks[rank]))
    return track_dict.keys()

def genPlaylist(sp, fc_tracks, singles_playlist_uri=None, selected_playlist_uri=None):
    singles_in = open('c:\\Users\\Jesse\\singles.txt', mode='r')
    for single in singles_in:
        single = single.strip()
        if len(single) == 0:
            continue
        vals = single.split(',')
        if vals[1] not in fc_tracks['singles']['tracks'].keys():
            fc_tracks['singles']['tracks'][vals[1]] = []
        fc_tracks['singles']['tracks'][vals[1]].append(vals[0])
        if vals[2] in fc_tracks['singles']['stats'].keys():
            fc_tracks['singles']['stats'][vals[2]] += 1
        else:
            fc_tracks['singles']['stats'][vals[2]] = 1
    singles_in.close()
    best_guess_in = open('c:\\Users\\Jesse\\best_guess.txt', mode='r')
    for best_guess in best_guess_in:
        best_guess = best_guess.strip()
        if len(best_guess) == 0:
            continue
        vals = best_guess.split(',')
        if vals[1] not in fc_tracks['selected']['tracks'].keys():
            fc_tracks['selected']['tracks'][vals[1]] = []
        fc_tracks['selected']['tracks'][vals[1]].append(vals[0])
        if vals[2] in fc_tracks['selected']['stats'].keys():
            fc_tracks['selected']['stats'][vals[2]] += 1
        else:
            fc_tracks['selected']['stats'][vals[2]] = 1
    best_guess_in.close()

    if singles_playlist_uri == None:
        playlist = sp.user_playlist_create(sp.current_user()[u'id'], 'Sorting Hat Singles Selection: ' + args.pubdate)
        singles_playlist_uri = playlist[u'uri']

    if selected_playlist_uri == None:
        playlist = sp.user_playlist_create(sp.current_user()[u'id'], 'Sorting Hat Best Guess Selection: ' + args.pubdate)
        selected_playlist_uri = playlist[u'uri']

    track_list = []
    for popularity in sorted(fc_tracks['singles']['tracks'].keys(), reverse=True):
        for track in fc_tracks['singles']['tracks'][popularity]:
            track_list.append(track)

    start = 0
    end = 99
    while start <= len(track_list):
        if end > len(track_list):
            end = len(track_list)
        sp.user_playlist_replace_tracks(sp.current_user()[u'id'], singles_playlist_uri, track_list[start:end])
        start += 100
        end += 100

    track_list = []
    for popularity in sorted(fc_tracks['selected']['tracks'].keys(), reverse=True):
        for track in fc_tracks['selected']['tracks'][popularity]:
            track_list.append(track)

    start = 0
    end = 99
    while start <= len(track_list):
        if end > len(track_list):
            end = len(track_list)
        sp.user_playlist_replace_tracks(sp.current_user()[u'id'], selected_playlist_uri, track_list[start:end])
        start += 100
        end += 100

    print('Singles')
    for position in fc_tracks['singles']['stats'].keys():
        print('{0}: {1}'.format(position, fc_tracks['singles']['stats'][position]))
    print('Selections')
    for position in fc_tracks['selected']['stats'].keys():
        print('{0}: {1}'.format(position, fc_tracks['selected']['stats'][position]))

if __name__ == "__main__":
    start_time = datetime.datetime.now()
    args = parser.parse_args()
    print args
    sp = getSpotifyConn()

    fc_date = datetime.datetime.strptime(args.pubdate, '%Y-%m-%d')

    album_count = 0
    fc_tracks = {}
    fc_tracks['singles'] = {}
    fc_tracks['singles']['tracks'] = {}
    fc_tracks['singles']['stats'] = {}
    fc_tracks['selected'] = {}
    fc_tracks['selected']['tracks'] = {}
    fc_tracks['selected']['stats'] = {}
    release_date_dict = {}
    # Get all new releases
    #results = getAlbumsFromNewReleases(sp)
    results = getAlbumsFromSortingHat()

    results = [x.__str__() for x in results]

    processed_in = open('c:\\Users\\Jesse\\tracks.txt')
    for album in processed_in:
        album = album.strip()
        if album in results:
            results.remove(album)
            album_count += 1
    processed_in.close()
    processed_out = open('c:\\Users\\Jesse\\tracks.txt', mode='a')
    singles_out = open('c:\\Users\\Jesse\\singles.txt', mode='a')
    best_guess_out = open('c:\\Users\\Jesse\\best_guess.txt', mode='a')
    for album in results:
        try:
            album_dets = sp.album(album)
        except Exception as e:
            print('Excpetion on ' + album.__str__())
            print(e)
            results.append(album)
            sp = getSpotifyConn()
            continue
        if len(album_dets[u'tracks'][u'items']) >= 3:
            release_date = release_date = datetime.datetime.strptime('1970-1-1', '%Y-%m-%d')
            try:
                release_date = datetime.datetime.strptime(album_dets[u'release_date'], '%Y-%m-%d')
            except:
                print('Bad date format: ' + album_dets[u'release_date'])
            if release_date in release_date_dict.keys():
                release_date_dict[release_date] += 1
            else:
                release_date_dict[release_date] = 1
            #print('{0} - {1} = {2}'.format(release_date, fc_date, release_date - fc_date))
            # Make sure the album released the week in question, not after, not before
            if release_date <= fc_date and release_date - fc_date > datetime.timedelta(days=-7):
                try:
                    [single, track, disc, track_num, artist_pop, track_name] = processAlbumDets(album_dets, sp, album_count)
                    #print('{0} pop {1}'.format(track_name, artist_pop))
                except Exception as e:
                    print('Excpetion on ' + album.__str__())
                    print(e)
                    results.append(album)
                    sp = getSpotifyConn()
                    continue
                if track == None:
                    continue
                track_list = None
                if single:
                    track_list = fc_tracks['singles']
                else:
                    track_list = fc_tracks['selected']
                if artist_pop not in track_list['tracks'].keys():
                    track_list['tracks'][artist_pop] = []
                track_list['tracks'][artist_pop].append(track)
                position = '_'.join([str(disc), str(track_num)])
                if position not in track_list['stats'].keys():
                    track_list['stats'][position] = 1
                else:
                    track_list['stats'][position] += 1
                if single:
                    singles_out.write(u','.join([track,str(artist_pop),position]) + '\n')
                    singles_out.flush()
                else:
                    best_guess_out.write(u','.join([track,str(artist_pop),position]) + '\n')
                    best_guess_out.flush()
                album_count += 1
                if album_count % 500 == 0:
                    sp = getSpotifyConn()
        processed_out.write(album + '\n')
        processed_out.flush()
    processed_out.close()
    singles_out.close()
    best_guess_out.close()

    for release_date in sorted(release_date_dict):
        print('{0}: {1}'.format(release_date, release_date_dict[release_date]))

    singlesPlaylistURI = 'spotify:user:audiobonsai:playlist:6z8m6hjBXxClAZt3oYONCa'
    selectedPlaylistURI = 'spotify:user:audiobonsai:playlist:626JCrZSTl0AQbO6vqr2MB'
    genPlaylist(sp, fc_tracks, singlesPlaylistURI, selectedPlaylistURI)

    for disc_number in sorted(stats_dict.keys()):
        for track_number in sorted(stats_dict[disc_number].keys()):
            pops = collections.OrderedDict(sorted(stats_dict[disc_number][track_number].items()))
            for popularity, count in pops.iteritems():
                print('{0}-{1}-{2}: {3}'.format(disc_number, track_number, popularity, count))

    end_time = datetime.datetime.now()
    total_time = end_time - start_time
    hours, remainder = divmod(total_time.seconds.__int__(), 3600)
    minutes, seconds = divmod(remainder, 60)
    print('Execution time: ' + '%s:%s:%s' % (hours, minutes, seconds))





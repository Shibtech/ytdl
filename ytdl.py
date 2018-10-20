from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import subprocess
import queue
import threading

# スレッド数
USER_THREAD = 5

# キューリスト
que_url = queue.Queue()

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "Your Develeper Key"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_BASEURL = "https://www.youtube.com/watch?v="
videos = []


def youtube_search(options):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
        q=options.q,
        part="id,snippet",
        maxResults=options.max_results
    ).execute()

    channels = []
    playlists = []
    videos_urls = []

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.

    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                 search_result["id"]["videoId"]))
            videos_urls.append(YOUTUBE_BASEURL + search_result["id"]["videoId"])

        elif search_result["id"]["kind"] == "youtube#channel":
            channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                   search_result["id"]["channelId"]))
        elif search_result["id"]["kind"] == "youtube#playlist":
            playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                    search_result["id"]["playlistId"]))


    while True:
        yeslist = []

        for i in range(len(videos)):
            print("以下をダウンロードしますか?(y/n)")
            print(videos[i])
            while True:
                r = input()
                if r == 'y':
                    yeslist.append("y")
                    break
                elif r == 'n':
                    yeslist.append("n")
                    break
                else:
                    print("もう一度入力してください")
                    continue
        print("\n\n以下のファイルをダウンロードします")

        if len(yeslist) == 0:
            print("１個も選択されていません")
            print("処理を中止します。")
            exit(0)

        for i in range(len(yeslist)):
            if yeslist[i] == 'y':
                print(videos[i])
        print("これでよろしいですか？(y/n)")
        r = input()

        if r == 'y':
            for i in range(len(videos_urls)):
                if yeslist[i] == 'y':
                    que_url.put(videos_urls[i])
            break
        else:
            print("ダウンロードを中止しますか?(y/n)")
            r = ''
            while r != 'y' and r != 'n':
                r = input()

            if r == 'y':
                print("処理を中止します")
                exit(1)
            elif r == 'n':
                continue

    for i in range(USER_THREAD):
        t = threading.Thread(target=handle_download)
        t.start()


def handle_download():
    while not que_url.empty():
        url = que_url.get()
        for video in videos:
            if video[-12:-2] in url:
                print("{}を処理します".format(video))
                res = subprocess.check_output(["youtube-dl", "-f", "mp4", url])
                print(res)


if __name__ == "__main__":
    argparser.add_argument("--q", help="Search term", default="Google")
    argparser.add_argument("--max-results", help="Max results", default=25)
    args = argparser.parse_args()

    try:
        youtube_search(args)
    except HttpError as e:
        print("An HTTP error occurred: \nstatus:{}\ncontent:{}".format(e.resp.status, e.content))

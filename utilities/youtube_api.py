import re

video_id_re = re.compile('youtube\.com/watch\?v=([^&]+)|youtube\.com/embed/([^\?])')

def get_video_id(url):
    """Youtube urls look like: http://www.youtube.com/watch?v=4DJozK30xJg where 4DJ...
    is the VIDEO_ID."""
    if not url:
        return ''
    video_id_match = re.search(video_id_re, url)
    vid_id = video_id_match.group(1) if video_id_match else ''
    return vid_id


if __name__ == '__main__':
    assert get_video_id('http://www.youtube.com/watch?v=ZwvpUuckoh8&autoplay=0') == 'ZwvpUuckoh8'
    assert get_video_id('http://www.youtube.com/watch?v=g0OwaqtH_hg') == 'g0OwaqtH_hg'
    assert get_video_id('something that should fail') == ''
    print 'tests pass.'
    
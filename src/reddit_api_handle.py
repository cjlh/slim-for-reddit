import requests
import datetime
import markdown2


class User(object):
    def __init__(self, json):
        self.username = json['data']['name']
        self.comment_karma = json['data']['comment_karma']
        self.link_karma = json['data']['link_karma']

        utc_time = json['data']['created']
        self.joined_timestamp = datetime.datetime.fromtimestamp(utc_time)
        self.joined_time_string = RedditApiHandle.utc_to_time_string(utc_time)

    def __str__(self):
        return self.username


class Post(object):
    def __init__(self, json):
        self.post_id = json['data']['id']
        self.title = json['data']['title']
        self.name = json['data']['name']
        self.url = json['data']['url']
        self.score = json['data']['score']
        self.author = json['data']['author']
        self.subreddit = json['data']['subreddit']

        self.comments = {
            'count': json['data']['num_comments'],
            'url': json['data']['permalink']
        }

        utc_time = json['data']['created_utc']
        self.timestamp = datetime.datetime.fromtimestamp(utc_time)
        self.time_string = RedditApiHandle.utc_to_time_string(utc_time)

    def __str__(self):
        return self.title


class PostList(object):
    def __init__(self, before, after, posts):
        self.before = before
        self.after = after
        self.posts = posts

    @classmethod
    def listing_json_to_postlist(cls, json):
        before = json['data']['before']
        after = json['data']['after']
        posts = []
        for post_data in json['data']['children']:
            post = Post(post_data)
            posts.append(post)
        return PostList(before, after, posts)


class Comment(object):
    def __init__(self, json):
        self.post_id = json['data']['id']
        self.gilded = json['data']['gilded']
        self.stickied = json['data']['stickied']
        self.archived = json['data']['archived']
        self.body = json['data']['body']
        self.body_html = \
            markdown2.markdown(json['data']['body'])\
            .replace('<p>', '<p class="comment-paragraph">')\
            .replace('<a ', '<a class="comment-hyperlink" ')\
            .replace('<p></p>', '')
        self.permalink = json['data']['permalink']
        self.score_hidden = json['data']['score_hidden']
        self.score = json['data']['score']
        self.author = json['data']['author']
        self.subreddit = json['data']['subreddit']
        self.controversiality = json['data']['controversiality']
        self.author_flair_text = json['data']['author_flair_text']

        utc_time = json['data']['created_utc']
        self.timestamp = datetime.datetime.fromtimestamp(utc_time)
        self.time_string = RedditApiHandle.utc_to_time_string(utc_time)

    def __str__(self):
        return self.body


class ThreadComment(Comment):
    def __init__(self, json, more=None, depth=0):
        Comment.__init__(self, json)

        self.depth = json['data']['subreddit']

        replies = json['data']['replies']
        self.replies = []

        if (len(replies) > 0):
            for reply in replies['data']['children']:
                if (reply['kind'] == 't1'):
                    self.replies.append(ThreadComment(reply, depth=depth + 1))
                elif(reply['kind'] == 'more'):
                    print('more')
                print('depth:', depth)


class ProfileComment(Comment):
    def __init__(self, json, more=None, depth=0):
        Comment.__init__(self, json)

        replies = json['data']['replies']
        self.replies = []

        if (len(replies) > 0):
            for reply in replies['data']['children']:
                if (reply['kind'] == 't1'):
                    self.replies.append(ProfileComment(reply))
                elif(reply['kind'] == 'more'):
                    print('more')


class CommentList(object):
    def __init__(self, before, after, comments, more):
        self.before = before
        self.after = after
        self.comments = comments
        self.more = more

    @classmethod
    def comments_json_to_commentlist(cls, listing_json, is_profile=False):
        before = listing_json['data']['before']
        after = listing_json['data']['after']
        comments = []
        more = None
        for comment_data in listing_json['data']['children']:
            if (comment_data['kind'] == 't1'):
                comment = ThreadComment(comment_data)\
                    if is_profile else ProfileComment(comment_data)
                comments.append(comment)
            elif (comment_data['kind'] == 'more'):
                # TODO: Make class for more?
                more = comment_data
        return CommentList(before, after, comments, more)


class RedditApiHandle:
    def __init__(self, client_id, client_secret):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Slim for Reddit'})
        self.session.auth = (client_id, client_secret)
        auth_post_data = {
            'grant_type': 'client_credentials'
        }
        r = self.session.post('https://www.reddit.com/api/v1/access_token',
                              auth_post_data)
        self.access_token = r.json()['access_token']

    def get_access_token(self):
        return self.access_token

    def get_user_details(self, username):
        request_url = 'https://www.reddit.com/user/' + username + \
            '/about/.json'
        r = self.session.get(request_url)
        return User(r.json())

    def get_post_details(self, post_id):
        fullname = 't3_' + post_id
        request_url = 'https://www.reddit.com/by_id/' + fullname + '/.json'
        r = self.session.get(request_url)
        post_json = r.json()['data']['children'][0]
        return Post(post_json)

    def get_posts_hot(self, path, limit):
        get_data = {
            'g': 'GLOBAL',
            'limit': limit
        }
        request_url = 'https://www.reddit.com' + path + 'hot/.json'
        r = self.session.get(request_url,
                             data=get_data)
        post_list = PostList.listing_json_to_postlist(r.json())
        return post_list

    def get_all_comments(self, post_id, limit, depth, sort='hot'):
        get_data = {
            'article': post_id,
            'limit': limit,
            'depth': 8,
            'sort': sort
        }
        request_url = 'https://www.reddit.com/comments/' + post_id + '/.json'
        r = self.session.get(request_url,
                             data=get_data)
        comment_list = CommentList.comments_json_to_commentlist(r.json()[1])
        return comment_list

    def get_profile_comments(self, username, limit, depth, sort='new'):
        get_data = {
            'context': 1,
            'limit': limit,
            'depth': 8,
            'sort': sort
        }
        request_url = 'https://www.reddit.com/user/' + username + \
            '/comments/.json'
        r = self.session.get(request_url,
                             data=get_data)
        comment_list = \
            CommentList.comments_json_to_commentlist(r.json(), True)
        return comment_list

    def get_profile_submissions(self, username, limit, sort='new'):
        get_data = {
            'context': 1,
            'limit': limit,
            'sort': sort
        }
        request_url = 'https://www.reddit.com/user/' + username + \
            '/submitted/.json'
        r = self.session.get(request_url,
                             data=get_data)
        post_list = \
            PostList.listing_json_to_postlist(r.json())
        return post_list

    def get_comment_context(self):
        return

    @staticmethod
    def utc_to_time_string(utc):
        time_delta = datetime.datetime.now() - \
            datetime.datetime.fromtimestamp(utc)
        num_days = time_delta.days
        num_secs = time_delta.seconds
        if (num_days > 0):
            if (num_days // 365 > 0):
                num_years = num_days // 365
                years_string = ' year ' if num_years == 1 else ' years '
                return str(num_years) + years_string + 'ago'
            elif (num_days // 30 > 0):
                num_months = num_days // 30
                months_string = ' month ' if (num_months == 1) else ' months '
                return str(num_days // 30) + months_string + 'ago'
            else:
                days_string = ' day ' if (num_days == 1) else ' days '
                return str(num_days) + days_string + 'ago'
        else:
            if (num_secs // 3600 > 0):
                num_hours = num_secs // 3600
                hours_string = ' hour ' if (num_hours == 1) else ' hours '
                return str(num_secs // 3600) + hours_string + 'ago'
            elif (num_secs // 60 > 0):
                num_mins = num_secs // 60
                mins_string = ' minute ' if (num_mins == 1) else ' minutes '
                return str(num_secs // 60) + mins_string + 'ago'
            else:
                secs_string = ' second ' if (num_secs == 1) else ' seconds '
                return str(num_secs) + secs_string + 'ago'

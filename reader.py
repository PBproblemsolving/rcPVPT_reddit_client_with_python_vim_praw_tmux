from credentials import ruser
from praw.models.reddit.subreddit import SubredditStream
#import fire
import datetime
from sys import stdout


def _stamptostring(timestamp):
    return str(datetime.datetime.utcfromtimestamp(timestamp))

def _attr_transformer(attr_value, string_template="{}", lambdaf= lambda x: x):
    return string_template.format(lambdaf(attr_value))

_submission_attrs = ('id', 'author', 'created_utc', 'subreddit', 'title', 
                     'num_comments', 'score', 'upvote_ratio', 'spoiler') 
_default_transformers = {}
_submission_attrs_dict = {key: _default_transformers 
                          for key in _submission_attrs}
_submission_attrs_dict['subreddit']={'string_template':"r/{}", 'lambdaf': 
                                     lambda x: getattr(x, 'display_name', "-")}
_submission_attrs_dict['id']={'string_template':"<<{}>>"}
_submission_attrs_dict['created_utc']={'lambdaf':lambda x: _stamptostring(x)}
_submission_attrs_dict['spoiler']={'string_template':'spoiler: {}'}
_submission_attrs_dict['num_comments']={'string_template':"\ncmnts: {}"}
_submission_attrs_dict['title']={'string_template':"\n{}"}

def _attrs_dict_factory(attrs_iter, value):
    return {key: value for key in attrs_iter}

def subreddit_submissions(sub_name, output=stdout, hot_new='hot', 
                          limit: int=20, stream=False, skip_existing=True):
    try:
        if stream:
            try:
                sub_name = ruser.subreddit(sub_name)
            except AttributeError as e:
                pass
            #for example: sub_name=reader.ruser.front
            sub = SubredditStream(sub_name).submissions(
                    skip_existing=skip_existing)
        else:
            #for example: sub_name=reader.ruser.front.hot
            sub = sub_name(limit=limit)
    except TypeError as e:
        if hot_new == 'new':    
            sub = ruser.subreddit(sub_name).new(limit=limit)
        if hot_new == 'hot':
            sub = ruser.subreddit(sub_name).hot(limit=limit)
    try: 
        output = open(output, 'w')
    except TypeError:
        pass

    for s in sub:
        s = ruser.submission(s)
        def line_to_write():
             for attr in _submission_attrs:
                yield _attr_transformer(getattr(s, attr, "-"),
                                       **_submission_attrs_dict.get(attr))

        output.write("; ".join(line_to_write()))
        output.write("\n")
    if output != stdout:
        output.close()

_comment_attrs = ('id_created_str', 'author', 'parent_id', 'body')
_comment_attrs_dict = _attrs_dict_factory(_comment_attrs, {})


def submission_coms(subs_id, output='output.txt'):
    c_submission = ruser.submission(subs_id)
    comments = c_submission.comments
    def iter_coms(comments, tabs):
        tabsstr = tabs*'\t'
        for c in comments:
            try:
                setattr(c, 'id_created_str', 
                        c.id + '; ' + _stamptostring(c.created_utc))
            except AttributeError:
                pass
            def line_to_write():
                for attr in _comment_attrs:
                    yield tabsstr + _attr_transformer(getattr(c, attr, "-"),
                                           **_comment_attrs_dict.get(attr))
            output.write("\n".join(line_to_write()))
            output.write("\n---\n")
            try:
                replies = c.replies
                iter_coms(replies, tabs+1)
            except AttributeError:
                if tabs == 0:
                    decision2 = input(
                            "should load more comments? y for yes: ")
                    if decision2 == 'y':
                        iter_coms(c.comments(), 0)
                    else:
                        continue
                else:
                    iter_coms(c.comments(), tabs)
            except Exception as e:
                print(e)
    try: 
        output = open(output, 'w')
    except TypeError:
        pass

    output.write(f"""{c_submission.name};\
            at {_stamptostring(c_submission.created_utc)};\
            by {c_submission.author.name}\n
            {c_submission.title}\n
            {c_submission.selftext or c_submission.url}\n---\n""")
    iter_coms(comments, 0)

    if output != stdout:
        output.close()


def _reply(to_what):
    def inner(*args):
        reply_object, details = to_what(*args)
        print('you are replying to:')
        print(details)
        print('with such content:')
        with open('input.md', 'r') as f:
            content = f.read()
        print(content)
        decision = input("do you want to proceed? y for yes: ")
        if decision == 'y':
            answer = reply_object.reply(content)
            print(f"your id {answer.id} and body: \n{answer.body}")
        else:
            print('aborted')
    return inner   

def create_submission(subreddit, title, url=None):
    subreddit = ruser.subreddit(subreddit)
    with open('input.md', 'r') as f:
            selftext = f.read()
    print('you are submitting to:')
    print(subreddit.display_name, subreddit.public_description, sep='\n')
    print("*******", 'with such content:', sep='\n')
    print(title, url or selftext, sep='\n')
    decision = input("do you want to proceed? y for yes: ")
    if decision == 'y':
        if url:
            subm = subreddit.submit(title, url=url)
            print(subm.title, subm.id, subm.subreddit, subm.url, sep='\n')
        else:
            subm = subreddit.submit(title, selftext=selftext)
            print(subm.title, subm.id, subm.subreddit, subm.selftext, sep='\n')
    else:
        print('aborted')


@_reply
def reply_comment(comment_id):
    obj = ruser.comment(comment_id)
    return obj, f"{obj.id}, {obj.body[:30]}"

@_reply
def reply_submission(submission_id):
    obj =  ruser.submission(submission_id)
    return obj, f"{obj.id}, {obj.title}"

@_reply
def reply_message(message_id):
    obj = ruser.inbox.message(message_id)
    return obj, f"{obj.id}, {obj.fullname} | {obj.body}"



#if __name__ == '__main__':
#    fire.Fire()

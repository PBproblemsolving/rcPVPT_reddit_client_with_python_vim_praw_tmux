from credentials import ruser
from praw.models import Submission
#import fire
import datetime


def _stamptostring(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp)

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

def _attrs_dict_factory(attrs_iter):
    return {key: {} for key in attrs_iter}

def subreddit_submissions(sub_name, out_file='output.txt', 
                   hot_new='hot', limit: int=20):
    try:
        #for example: sub_name=reader.ruser.front.hot
        sub = sub_name(limit=limit)
    except TypeError:
        if hot_new == 'new':    
            sub = ruser.subreddit(sub_name).new(limit=limit)
        if hot_new == 'hot':
            sub = ruser.subreddit(sub_name).hot(limit=limit)
    with open(out_file, 'w') as f:
        for s in sub:
            s = ruser.submission(s)
            def line_to_write():
                 for attr in _submission_attrs:
                    yield _attr_transformer(getattr(s, attr, "-"),
                                           **_submission_attrs_dict.get(attr))

            f.write("; ".join(line_to_write()))
            f.write("\n")

_comment_attrs = ('id', 'author', 'parent_id', 'body')
_comment_attrs_dict = _attrs_dict_factory(_comment_attrs)

def submission_coms(subs_id, out_file='output.txt'):
    c_submission = ruser.submission(subs_id)
    comments = c_submission.comments
    def iter_coms(comments, tabs):
        tabsstr = tabs*'\t'
        for c in comments:
            def line_to_write():
                for attr in _comment_attrs:
                    yield tabsstr + _attr_transformer(getattr(c, attr, "-"),
                                           **_comment_attrs_dict.get(attr))
            f.write("\n".join(line_to_write()))
            f.write("\n---\n")
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
    with open(out_file, 'w') as f:
        f.write(f"{c_submission.name}: \n \
                {c_submission.selftext or c_submission.url}\n---\n")
        iter_coms(comments, 0)

def _reply(to_whom):
    def inner(*args):
        reply_object, details = to_whom(*args)
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
    print('with such content:')
    print(title, url if url else selftext, sep='\n')
    decision = input("do you want to proceed? y for yes: ")
    if decision == 'y':
        if url:
            subm = subreddit.submit(title, url=url)
            print(subm.title, subm.id, subm.subreddit, subm.url, sep='\n')
        else:
            subm = subreddit.submit(title, selftext=selftext)
            print(subm.title, subm.id, subm.subreddit, subm.body, sep='\n')
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

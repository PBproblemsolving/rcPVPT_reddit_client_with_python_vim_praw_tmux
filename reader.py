from credentials import ruser
from praw.models import Submission
import fire
import datetime


def stamptostring(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp)

def attr_transformer(attr_value, string_template="{}", lambdaf= lambda x: x):
    return string_template.format(lambdaf(attr_value))

submission_attrs = ('author', 'created_utc', 'id', 'title', 'num_comments', 
                    'score', 'upvote_ratio', 'spoiler') 
default_transformers = {}
submission_attrs_dict = {key: default_transformers for key in submission_attrs}
submission_attrs_dict['id']={'string_template':"id: <<{}>>"}
submission_attrs_dict['created_utc']={'lambdaf':lambda x: stamptostring(x)}
submission_attrs_dict['spoiler']={'string_template':'spoiler: {}'}
submission_attrs_dict['num_comments']={'string_template':"cmnts: {}"}

def attrs_dict_factory(attrs_iter):
    return {key: {} for key in attrs_iter}

def subreddit_subs(sub_name, hot_new='hot', limit: int=20):
    if hot_new == 'new':    
        sub = ruser.subreddit(sub_name).new(limit=limit)
    if hot_new == 'hot':
        sub = ruser.subreddit(sub_name).hot(limit=limit)
    with open('output.txt', 'w') as f:
        for s in sub:
            s = ruser.submission(s)
            def line_to_write():
                 for attr in submission_attrs:
                    yield attr_transformer(getattr(s, attr, "-"),
                                           **submission_attrs_dict.get(attr))

            f.write("; ".join(line_to_write()))
            f.write("\n")

comment_attrs = ('author', 'id', 'parent_id', 'body')
comment_attrs_dict = attrs_dict_factory(comment_attrs)

def submission_coms(subs_id):
    c_submission = ruser.submission(subs_id)
    comments = c_submission.comments
    def iter_coms(comments, tabs):
        tabsstr = tabs*'\t'
        for c in comments:
            def line_to_write():
                for attr in comment_attrs:
                    yield tabsstr + attr_transformer(getattr(c, attr, "-"),
                                           **comment_attrs_dict.get(attr))
            try:
                f.write("\n".join(line_to_write()))
                f.write("\n---\n")
            except AttributeError:
                iter_coms(c.comments(), 0)
            try:
                replies = c.replies
                iter_coms(replies, tabs+1)
            except Exception as e:
                print(e)
    with open('output.txt', 'w') as f:
        f.write(f"{c_submission.name}: \n \
                {c_submission.selftext or c_submission.url}\n")
        iter_coms(comments, 0)

def reply(to_whom):
    def inner(*args):
        reply_object, details = to_whom(*args)
        print('you are replying to:')
        print(details)
        print('with such content:')
        with open('input.txt', 'r') as f:
            content = f.read()
            print(content)
            decision = input("do you want to proceed? y for yes: ")
            if decision == 'y':
                answer = reply_object.reply(content)
                print(f"your id {answer.id} and body: \n{answer.body}")
            else:
                print('aborted')
    return inner   

@reply
def reply_comment(comment_id):
    obj = ruser.comment(comment_id)
    return obj, f"{obj.id}, {obj.body[:30]}"

@reply
def reply_submission(submission_id):
    obj =  ruser.submission(submission_id)
    return obj, f"{obj.id}, {obj.title}"



if __name__ == '__main__':
    fire.Fire()

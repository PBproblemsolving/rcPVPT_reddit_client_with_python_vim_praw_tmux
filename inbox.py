from credentials import ruser
from reader import _stamptostring

if __name__ == '__main__':
    for i in ruser.inbox.unread():
        creation_time = _stamptostring(i.created_utc)
        print(f"{i.author.name}:\t{creation_time}:\t{i.id}\n{i.body}")
    for i in ruser.inbox.stream():
        creation_time = _stamptostring(i.created_utc)
        print(f"{i.author.name}:\t{creation_time}:\t{i.id}\n{i.body}")
        ruser.inbox.mark_read([i])


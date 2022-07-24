#!/usr/bin/env python3
from git import Repo
from github import Github
import dbm
import json
import re
import time
import os.path
import os
import argparse


config = []
cmdargs = []
issue_pattern = ""
cache = None

def loadConfig():
    os.makedirs(os.getenv("HOME") + "/.config/tivoli-review", exist_ok=True)

    with open(os.getenv('HOME') + "/.config/tivoli-review/tivoli-review.json") as cf:
        data = cf.read()
        return json.loads(data)

def loginToGithub():
    with open("/home/vadim/.github-tivoli.token", "r") as keyfile:
        key = keyfile.readline().rstrip()
        g = Github(key)

        return g

def loadPattern():
    os.makedirs(os.getenv("HOME") + "/.config/tivoli-review", exist_ok=True)

    for file in [os.getenv("HOME") + "/.config/tivoli-review/issue.md", "issue.md"]:
        if os.path.exists(file):
            with open(file) as fh:
                data = fh.read()
                return data;


def updateCache(repo):
    print("Updating issue cache...")
    updates = 0
    for issue in repo.get_issues(state="all"):
        ret = storeIssueInCache(issue)

        if ret:
            updates = updates + 1
            if cmdargs["only_one"]:
                print("Stopping after one cache update.")
                return

    print("Done, {count} updates made.".format(count=updates))

def storeIssueInCache(issue):
    m = re.fullmatch('^Import ([0-9a-f]+): (.*?)$', issue.title)

    if m:
        commit = m.group(1)

        print("Issue #{number}: {title}".format(number = issue.number, title=issue.title))

        cache_data = {}
        if commit in cache:
            cache_data = json.loads(cache[commit])

        issue_data = { "id" : issue.id, "number" : issue.number, "body" : issue.body, "title": issue.title}


        data = json.dumps(issue_data, sort_keys = True)

        if not commit in cache:
            print("\tIssue not in cache, storing")
            if not cmdargs["dry_run"]:
                cache[commit] = data

            return True

        if cache_data != issue_data:
            print("\tIssue data different from cache")

            if cmdargs["debug"]:
                if (cache_data["id"] != issue_data["id"]):
                    print("ID    : {a}/{b}".format(a = cache_data["id"], b = issue_data["id"]))
                if (cache_data["number"] != issue_data["number"]):
                    print("number: {a}/{b}".format(a = cache_data["number"], b = issue_data["number"]))
                if (cache_data["title"] != issue_data["title"]):
                    print("title : {a}/{b}".format(a = cache_data["title"], b = issue_data["title"]))
                if (cache_data["body"] != issue_data["body"]):
                    print("body  : {a}/{b}".format(a = cache_data["body"], b = issue_data["body"]))


            if cache_data["body"] == issue_data["body"]:
                print("\tDuplicated issue, ignoring.")
                return False
            else:
                print("\tModified issue, updating.")
                if not cmdargs["dry_run"]:
                    cache[commit] = data

            return True
        else:
            print("\tAlready cached")
            return False

        return False
    else:
        print("Not adding issue " + str(issue.id) + " to cache, doesn't look like ours: '" + issue.title + "'")
        return False



def hasIssue(repo, commit):
        return commit in cache

#        if repo.get_issues(


def createIssue(git_repo, repo, commit):
    shortsha = commit.hexsha[0:10]


    message_lines = commit.message.splitlines();
    first_line = message_lines[0]
    message_lines.pop(0)
    short_sha = commit.hexsha[0:10]
    human_time = time.strftime("%a, %d %b %Y %H:%M", time.gmtime(commit.committed_date))


    stats_data = ""
    total_in_blame = 0

    for file, data in commit.stats.files.items():
#        print("F: " + str(file))
        if stats_data != "":
            stats_data = stats_data + "\n"



        blameinfo = "⚠ 0"
        if os.path.exists(config["repository"]["path"] + "/" + file):
            blame_data = git_repo.blame('HEAD', file=file)
            found = 0
            for row in blame_data:
                row_commit = row[0]
                row_lines = row[1]
#                print("Commit {commit}, lines {lines}".format(commit=row_commit, lines=len(row_lines)))
#                print("Cur is {commit}, match is = {match}".format(commit=commit.hexsha, match = row_commit == commit.hexsha))


                if row_commit.hexsha == commit.hexsha:
                    found = found + len(row_lines)
                    blameinfo = str(found)
                    total_in_blame = total_in_blame + len(row_lines)
        else:
            blameinfo = "⚠ File gone"

#                print("Commit {commit}: {lines} lines".format(commit=commit, lines=lines.count()))

#            print(str(blame_data))

        stats_data = stats_data + "| {file} | {stats} | {lines} | {added} | {removed} | {blame}".format(file=file, stats="", lines=data["lines"], added=data["insertions"], removed=data["deletions"], blame=blameinfo)


    body = issue_pattern
    ts = commit.stats.total

    body = body.replace("%COMMIT_ID%", commit.hexsha)
    body = body.replace("%AUTHOR%", commit.author.name)
    body = body.replace("%DATE%", human_time)
    body = body.replace("%MESSAGE%", commit.message)
    body = body.replace("%FILESTATS%", stats_data)
    body = body.replace("%TOTAL_FILES%", str(ts["files"]))
    body = body.replace("%TOTAL_LINES%", str(ts["lines"]))
    body = body.replace("%TOTAL_ADDED%", str(ts["insertions"]))
    body = body.replace("%TOTAL_REMOVED%", str(ts["deletions"]))
    body = body.replace("%TOTAL_IN_BLAME%", str(total_in_blame))


    subject = "Import {shortsha}: {first_line} (by {author})".format(shortsha = shortsha, first_line = first_line, author=commit.author.name)

    if cmdargs["debug"]:
        print("SUBJ: " + subject)
        print("BODY:\n" + body)
        print("==========================")


    if shortsha in cache:
        data = json.loads(cache[shortsha])

        if data["title"] == subject and data["body"] == body:
            print("\tIssue already existed, skipping")
            return False
        else:
            print("Issue {num} will be updated".format(num=data["number"]))
            issue = repo.get_issue(data["number"])

            labels = []

            for l in issue.labels:
                labels.append(l.name)

            if not "automanaged" in labels:
                labels.append("automanaged")



            if not cmdargs["dry_run"]:
                issue.edit(subject, body, labels=labels)

                new_data = json.dumps({ "id" : issue.id, "number": issue.number, "body" : body, "title": subject})
                cache[shortsha] = new_data
                time.sleep(config["github"]["limits"]["issue-delay"])
            return True


    if not cmdargs["dry_run"]:
        issue = repo.create_issue(subject, body, labels=["automanaged"])

        new_data = json.dumps({ "id" : issue.id, "number": issue.number, "body" : body, "title": subject})
        cache[shortsha] = new_data

        time.sleep(config["github"]["limits"]["issue-delay"])
    return True

#    title = "Import " + shortsha + ": " + first_line + "(" + commit.author.name + ")"

def deduplicate(gh_repo):
    seen = {}

    for issue in gh_repo.get_issues(sort='created', direction='asc'):
        print("Issue {number}: {title}".format(number=issue.number, title=issue.title))
        m = re.fullmatch('^Import ([0-9a-f]+): (.*?)$', issue.title)

        if m:
            commit = m.group(1)
            if commit in seen:
                print("\tDuplicated! Seen before as issue " + str(seen[commit]))

                if not cmdargs["dry_run"]:
                    issue.create_comment("Duplicate of #{number}".format(number=seen[commit]))
                    issue.edit(state="Closed")
                    time.sleep(config["github"]["limits"]["issue-delay"])

                    if cmdargs["only_one"]:
                        print("Stopping after one issue.")
                        os._exit(1)

            seen[commit] = issue.number





cmdparser = argparse.ArgumentParser(description="Tivoli Review Helper", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
cmdparser.add_argument("-v", "--verify", action="store_true", help="Verify the configuration")
cmdparser.add_argument("--dry-run", action="store_true", help="Don't update github, only pretend to do work.")
cmdparser.add_argument("-C", "--update-cache", action="store_true", help="Force an update of the issue cache")
cmdparser.add_argument("-D", "--debug", action="store_true", help="Output debug information")
cmdparser.add_argument("-1", "--only-one", action="store_true", help="Only process one commit. For testing.")
cmdparser.add_argument("--deduplicate", action="store_true", help="Remove duplicated issues from GitHub")

cmdargs = vars(cmdparser.parse_args())


#print(str(cmdargs))
#os._exit(1)

# Load config
config = loadConfig()
issue_pattern = loadPattern()

os.makedirs(os.getenv("HOME") + "/.local/share/tivoli-review", exist_ok=True)
cache = dbm.open(os.getenv("HOME") + "/.local/share/tivoli-review/issue_cache", "c")


# Init github
gh = Github(config["github"]["key"])
gh_repo = gh.get_organization(config["github"]["organization"]).get_repo(config["github"]["repository"])



if cmdargs["update_cache"]:
    updateCache(gh_repo)
    os._exit(0)


git_repo = Repo(config["repository"]["path"])
assert not git_repo.bare

commits = list(git_repo.iter_commits(config["repository"]["branch"], max_count = config["repository"]["commit-backlog"]))
commits.reverse()

processed = 0
added = 0

if cmdargs["verify"]:
    print("Configuration verified.")
    os._exit(0)

if cmdargs["deduplicate"]:
    deduplicate(gh_repo)
    os._exit(0)

for commit in commits:

    if not commit.author.email in config["repository"]["whitelisted-authors"]:
        continue

    if added > config["github"]["limits"]["issue-limit"]:
        print("Issue limit reached, stopping here.")
        break

    message_lines = commit.message.splitlines();
    first_line = message_lines[0]
    message_lines.pop(0)
    short_sha = commit.hexsha[0:10]


    print(short_sha + " " + commit.author.name + " " + commit.author.email + " " + first_line)

    #if not hasIssue(gh_repo, short_sha):

    if createIssue(git_repo, gh_repo, commit):
        print("\tIssue created/updated!")
        added = added + 1
    else:
        print("\tIssue already exists, skipping it!")

    processed = processed + 1

    if cmdargs["only_one"]:
        print("Stopping after one commit.")
        os._exit(1)

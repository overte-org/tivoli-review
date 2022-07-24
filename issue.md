This is an automated proposal to look at a commit made by %AUTHOR% and import it into [Overte](https://github.com/overte-org/overte)

| **Commit:** |  %COMMIT_ID% |
| --- | --- |
| **Author:** | %AUTHOR% |
| **Date:** | %DATE% |

```
%MESSAGE%
```


**Stats:**

| **Filename** | Stats | Lines | Added | Removed | Lines in blame |
| --- |  --- | --- | --- | --- | --- |
%FILESTATS%
| %TOTAL_FILES% files | - | %TOTAL_LINES% | %TOTAL_ADDED% | %TOTAL_REMOVED% | %TOTAL_IN_BLAME% |


To work on this, please assign the issue to yourself, then look at the commit and decide whether this would be a good addition to Overte.

* If the commit is useful, tag it with "Tivoli: Keep", and keep it open until it's merged.
* If the commit is not useful, tag it with "Tivoli: Discard", and close it.
* If the commit is not useful right now, but might be later, tag it with "Tivoli: Maybe later", and close it.
* If it's hard to decide, tag it with "Tivoli: Discuss", and keep it open.

Useful commits should be submitted as a [PR against Overte](https://github.com/overte-org/overte/pulls). Tag this issue in PR, so that it's automatically closed once the PR is merged.

You can cherry-pick this issue with this command:

    git cherry-pick %COMMIT_ID%

# Spec Kit Git: Create Feature Branch

Invoked as a mandatory `before_specify` hook. Creates (or switches to) a git
feature branch named after the upcoming feature, before `/speckit-specify`
creates the spec directory.

## Task

1. Read the feature description from the user input — it is the same text that
   was passed to `/speckit-specify`.

2. Run the branch creation script, passing the feature description as the argument:

   ```
   bash .specify/scripts/bash/git-create-branch.sh "<feature_description>"
   ```

   Use shell quoting so descriptions with spaces and special characters are
   passed as a single argument.

3. Capture the JSON output from the script. It has the form:
   `{"BRANCH_NAME":"003-my-feature","FEATURE_NUM":"003"}`

4. Print the JSON output exactly as received (do not reformat it). This is what
   `/speckit-specify` reads to know which branch was created.

## Edge cases

- If the feature description is empty, run the script with an empty string and
  let the script decide (it will error and exit non-zero — surface that error).
- If the user provided `GIT_BRANCH_NAME` explicitly, append `--short-name
  "<GIT_BRANCH_NAME>"` to the script invocation so the branch uses that exact
  name.
- The script writes progress messages to stderr (e.g. "Created branch 003-auth");
  only the JSON line goes to stdout. Print only the JSON to the user.

## Done when

- The git branch exists and is checked out (`git branch --show-current` matches
  `BRANCH_NAME` in the JSON output).
- JSON containing `BRANCH_NAME` and `FEATURE_NUM` has been output.

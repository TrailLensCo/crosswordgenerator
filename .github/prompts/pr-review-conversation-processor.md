# PR Review Conversation Processor

<!--
This prompt is designed to iterate through all review conversations in an active Pull Request,
address each comment by either fixing the code or explaining why it doesn't apply, and then
resolve each conversation item.

Usage:
1. Open the PR in GitHub or VS Code
2. Copy this prompt to GitHub Copilot chat
3. The assistant will process all review conversations systematically
-->

## Task Overview

Process all review conversations in the active Pull Request by:
1. Identifying all unresolved review comments
2. For each comment, determine if it requires a code change
3. If applicable, fix the issue in the code and mark as resolved
4. If not applicable, comment explaining why and mark as resolved
5. Continue until all conversations are resolved

## Context

- **Repository**: Current repository with an active Pull Request
- **Branch**: Feature branch with pending review conversations
- **Goal**: Address all reviewer feedback systematically and completely

## Requirements

### 1. Review Conversation Discovery
- Use GitHub Pull Request tools to fetch the active PR details
- Identify all review comments and conversations
- Parse conversation threads to understand context
- Prioritize unresolved conversations

### 2. Comment Analysis
- Read each comment and understand the reviewer's concern
- Determine if the comment requires:
  - Code changes (bug fix, refactoring, improvement)
  - Documentation updates
  - Test additions/modifications
  - Explanation only (comment already addressed, out of scope, etc.)

### 3. Code Changes (When Applicable)
- Locate the relevant file(s) mentioned in the comment
- Read the current code for context
- Implement the requested change following project standards
- Verify the change addresses the reviewer's concern
- Run relevant tests if applicable
- Add a reply comment summarizing the fix
- Mark the conversation as resolved

### 4. Explanation (When Not Applicable)
- Draft a clear, professional response explaining:
  - Why the change is not applicable
  - What was already done to address the concern
  - Why the current approach is preferred
  - Reference relevant documentation or previous discussions
- Post the explanation as a reply comment
- Mark the conversation as resolved (if appropriate)

### 5. Progress Tracking
- Maintain a list of processed conversations
- Track which conversations have been resolved
- Ensure no conversations are skipped or missed
- Provide status updates after processing each comment

## Expected Behavior

After running this prompt:
- All unresolved PR review conversations are processed
- Code changes are implemented where appropriate
- Clear explanations are provided where changes are not applicable
- **All conversations are AUTOMATICALLY resolved using GitHub API/CLI** (not left for manual resolution)
- Verification confirms zero unresolved conversations remain
- The PR is ready for re-review or approval

## Workflow Steps

### Step 1: Fetch PR Information
```
1. Get the active pull request details
2. List all review comments and conversations
3. Identify which conversations are unresolved
4. Create a prioritized list to process
```

### Step 2: Process Each Conversation
```
For each unresolved conversation:
  a. Read the comment thread
  b. Understand the reviewer's request/concern
  c. Locate the relevant code
  d. Determine if code changes are needed
  
  If code change needed:
    - Read surrounding code for context
    - Implement the fix/improvement
    - Test if applicable
    - Reply: "Fixed in [commit/file]: [brief description]"
    - Resolve the conversation
  
  If explanation needed:
    - Draft professional response
    - Explain why change is not applicable
    - Provide context or alternatives
    - Reply with explanation
    - Resolve the conversation (if appropriate)
```

### Step 3: Verification
```
1. Verify all conversations have been addressed
2. Check that all code changes are consistent
3. Ensure no new issues were introduced
4. Confirm all resolutions are appropriate
```

## Instructions for AI Assistant

**IMPORTANT**:

- **DO NOT** skip any review conversations
- **DO NOT** resolve conversations without addressing them first
- **DO NOT** leave conversations unresolved - YOU MUST RESOLVE THEM programmatically
- **DO NOT** ask the user to manually resolve conversations in GitHub UI
- **DO NOT** make assumptions about what the reviewer meant - ask for clarification if unclear
- **DO** provide clear, concise responses to each comment
- **DO** follow the project's coding standards (see `.github/CONSTITUTION.md`)
- **DO** test changes when applicable
- **DO** maintain a professional, collaborative tone in all responses
- **DO** use GitHub API/CLI to programmatically resolve each conversation after addressing it

**Process**:

1. Fetch the active PR and all review conversations using GitHub PR tools
2. Create a TODO list of all conversations to process
3. Process conversations one at a time in order
4. For each conversation:
   - Read and understand the comment
   - Analyze the relevant code
   - Either fix the code OR prepare an explanation
   - Reply to the conversation with your fix/explanation
   - **IMMEDIATELY resolve the conversation using GitHub CLI/API** (do NOT leave for manual resolution)
5. Verify ALL conversations are marked as resolved
6. Provide a summary of resolved conversations
7. Ask if any follow-up is needed

**Response Guidelines**:

When making code changes:
- Reply: "✅ Fixed: [brief description of what was changed]"
- Reference the specific file and lines changed
- Explain the solution if not obvious

When explaining why a change doesn't apply:
- Reply: "ℹ️ [Clear explanation]"
- Be specific about why the concern doesn't apply
- Provide context or reference documentation
- Suggest alternatives if helpful

**Success Criteria**:

- [ ] All unresolved review conversations identified
- [ ] Each conversation addressed appropriately
- [ ] Code changes implemented where needed
- [ ] Clear explanations provided where changes not applicable
- [ ] All conversations resolved with comments
- [ ] No conversations skipped or missed
- [ ] PR is ready for re-review

## Additional Notes

### Edge Cases to Consider
- Comments that are informational only (no action required)
- Comments that conflict with each other
- Comments that require discussion before resolution
- Comments on deleted or moved code
- Comments that reference external dependencies or blocked work

### Best Practices
- Keep responses concise but informative
- Link to relevant documentation when explaining decisions
- If uncertain about a comment's intent, ask the reviewer for clarification before resolving
- Group related fixes in a single commit when appropriate
- Update tests if behavior changes
- Consider reviewer's expertise and perspective when responding

### When to NOT Resolve
- Comment requires further discussion with the team
- Comment suggests a breaking change that needs approval
- Comment identifies an issue that requires significant refactoring
- Comment is unclear and needs clarification from the reviewer

In these cases, reply with questions or discussion points but leave the conversation open for the reviewer to respond.

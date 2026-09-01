# Safety & Architecture Review Template

Review this change before editing or approving it.

## Rules

- Do not edit files unless I explicitly ask.
- Give feedback first.
- Focus on security, architecture, maintainability, and simplicity.
- Point out risky patterns clearly.
- Suggest the smallest safe improvement.
- Avoid overengineering.

## Security checklist

Check if the code:

- Validates all user inputs before using them.
- Treats every user input as potentially unsafe.
- Avoids exposing raw errors, stack traces, API responses, URLs, or secrets in the UI.
- Logs technical errors internally instead of showing them to the user.
- Does not print API keys, tokens, `.env` values, or sensitive data.
- Avoids injecting user input directly into prompts without validation or clear boundaries.
- Handles prompt-injection attempts where relevant.
- Uses generic user-facing error messages.
- Keeps `.env` out of Git.
- Uses `.env.example` for required environment variables.

## Error handling checklist

Check if the code:

- Shows friendly user-facing errors.
- Logs the real technical error with `logging.exception()`.
- Does not use `st.code(str(error))` or expose raw exceptions to users.
- Handles expected failure cases gracefully.
- Retries only transient errors such as timeouts, connection errors, or 5xx responses.
- Does not retry 4xx errors such as invalid requests, bad model IDs, or auth errors.

## Architecture checklist

Check if the code keeps responsibilities separated:

- UI / Streamlit logic stays in `app.py`.
- API calls stay in client modules such as `openrouter_client.py`.
- Validation and safety logic stays in `security.py`.
- Prompts stay in `prompts.py` or prompt template files.
- Tools stay in dedicated tool modules.
- RAG logic stays in dedicated retrieval/vector-store modules.
- Tests stay in `tests/`.

Check if the change:

- Is small and focused.
- Does not mix unrelated concerns.
- Avoids large refactors unless necessary.
- Keeps function names clear and specific.
- Avoids generic functions like `process_everything()`.
- Makes the code easier to test.

## Tool / agent checklist

If the change involves tools or agents, check:

- Each tool has one clear purpose.
- Tool names are specific.
- Tool descriptions clearly explain when to use the tool.
- Tool parameters are explicit and validated.
- The system avoids over-eager tool use.
- The final answer is based on tool results when tools are used.
- Tool failures are handled safely.

## RAG checklist

If the change involves RAG, check:

- Documents are loaded from clear sources.
- Chunking strategy is reasonable.
- Retrieved context is shown or traceable.
- Sources/citations are displayed when useful.
- The model is instructed to answer from retrieved context.
- The app handles missing or weak context.
- The system avoids pretending retrieved context is complete when it is not.

## Testing checklist

Check if the change should include or update tests.

Prioritize tests for:

- Input validation.
- Prompt-injection blocking.
- Offensive-language blocking.
- Tool selection.
- Parameter extraction.
- RAG retrieval behavior.
- Error handling.

## Output format

Respond with:

1. Summary of the change
2. Main risks found
3. Must-fix issues
4. Nice-to-have improvements
5. Minimal safe next step
6. How to test it


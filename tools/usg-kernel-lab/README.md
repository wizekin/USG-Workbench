# USG Kernel Lab

USG Kernel Lab is a small website that runs on your own computer. It lets you try how the current USG software reads text, organizes information, and applies a limited set of reasoning rules.

You do **not** need programming experience to use the main screens. Write a sentence, choose English or Modern Standard Arabic, and select an analysis button. The results are shown in tables with everyday explanations.

## Start the lab on Windows

1. Open Command Prompt or PowerShell.
2. Go to the main folder of this repository.
3. Start the local server:

   ```powershell
   py tools/usg-kernel-lab/server.py
   ```

4. Open this address in your browser: [http://127.0.0.1:8765](http://127.0.0.1:8765).
5. To stop the lab, return to the command window and press **Ctrl+C**.

The server listens only on your own computer. The lab does not send your text to a cloud service and does not require a paid API.

## A beginner's guide

### 1. Try a sentence with the basic reader

Write a short sentence in the first text box. Choose English or Modern Standard Arabic, then select **Analyze my text**.

The result table shows what the basic reader could turn into structured information. You may see that some words were recognized while others were left unresolved or unsupported. That is useful test information, not necessarily a mistake in your input.

### 2. See the detailed reading

The second text box runs the Phase 5 analysis. It shows the stages the software currently supports, such as recognizing words, splitting the text into parts, examining word order, combining possible meanings, and suggesting possible links between parts of the text.

A suggested link is only a possibility. It does not prove that two words refer to the same person or thing. Use **More detailed tools** only when you need to compare a saved analysis or inspect the built-in reference information.

### 3. Try a prepared reasoning example

Choose one of the examples in the reasoning section and select **Run this example**. Each example contains information and rules prepared for the test. The result shows whether those rules support the requested conclusion.

These examples test a limited, structured reasoning ability. They are not ordinary free-form questions, and passing them does not mean that USG can understand every question.

### 4. Save and revisit your work

The save area stores structured documents in a local SQLite database. You can give a document a name, save a new version, reopen a saved version, and check that it has not unexpectedly changed.

- **Show when statements apply** displays conditions and exceptions attached to statements.
- **Show statements that disagree** looks for statements that conflict under the same conditions. It does not automatically choose which statement is correct.
- **Download the structured document** saves a copy in the USG machine-readable format.

### 5. Advanced tools

Most users can ignore this area. It is for people who already have a USG-SEM/1.0 structured document or need to edit the internal links between words and the people, things, or ideas they refer to.

The small reference codes are internal connection labels. They are not ordinary words and are not intended to be guessed.

## What the results mean

| What you may see | Plain-English meaning |
|---|---|
| Complete | The operation finished for the parts this version knows how to process. It does not mean every meaning was understood. |
| Partial | Some information was processed, but some parts were left out or could not be handled. |
| Unsupported | This version does not have a rule for that part of the input. |
| Unresolved | The system found a word or phrase but could not determine what it refers to. |
| Ambiguous | More than one possible meaning or connection remains. |
| Possible answer / candidate | A suggestion produced by the system. It is not automatically confirmed. |
| Rule explanation / derivation | The steps showing how a stored rule led to a possible conclusion. |
| Contradiction | Two statements appear to disagree in the same situation. The lab does not decide which one is true. |
| Saved version | A copy of a document kept so it can be reopened later. Earlier versions are not silently overwritten. |

## Important limits

- The English and Arabic interpreters are limited demonstrations, not general-purpose language readers.
- The basic reader and the detailed Phase 5 reader are different systems. Their outputs should not be treated as interchangeable.
- Phase 5 shows analysis stages and possible connections. It does **not** create a complete USG-SEM/1.0 document.
- A result marked as complete only describes the operation that was run. It is not proof that the interpretation is complete, correct, or true.
- Unknown, unclear, unsupported, and conflicting information should remain visible rather than being guessed away.

## Developer information

The interface is served by `tools/usg-kernel-lab/server.py` and its page is `tools/usg-kernel-lab/index.html`.

Requirements:

- Python 3.10 or newer
- `jsonschema>=4.18,<5`

Install the dependency from the repository root:

```powershell
py -m pip install "jsonschema>=4.18,<5"
```

The default database is `usg-workbench.sqlite3` in the repository root. To choose a different location:

```powershell
py tools/usg-kernel-lab/server.py --db D:\USGData\usg-workbench.sqlite3
```

The local server binds only to `127.0.0.1`.

### Local API

The versioned API remains available for developers and automated tests:

- `POST /v1/validate`
- `POST /v1/documents`
- `GET /v1/documents/{document_id}?revision=N`
- `GET /v1/documents/{document_id}/check?revision=N`
- `GET /v1/documents/{document_id}/revisions`
- `GET /v1/documents/{document_id}/conditions?revision=N`
- `GET /v1/documents/{document_id}/contradictions?revision=N`
- `GET /v1/documents/{document_id}/export?revision=N`
- `POST /v1/query`
- `POST /v1/interpret`
- `GET /v2/resources`
- `POST /v2/interpret`
- `GET /v2/interpretations`
- `GET /v2/interpretations/{run_id}`
- `GET /v2/interpretations/{run_id}/export`
- `POST /v2/interpretations/{run_id}/replay`
- `POST /v2/associations`
- `GET /v2/associations?source_ref=...`

The SQLite database remains the only persistence store used by the lab.
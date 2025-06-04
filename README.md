# CallGraphite

CallGraphite is a Neovim plugin aimed at exploring large codebases by collecting function bodies and sending them to language models (LLMs) for analysis. The plugin traverses the project using the Language Server Protocol (LSP) in a depth-first search (DFS) manner, gathering the text for each function it encounters. This allows you to quickly feed relevant portions of your code to an LLM for tasks such as summarisation or understanding call graphs.

## Installation

Use your favourite Neovim plugin manager. Examples are shown below.

### Using Plug

```vim
Plug 'mikewong23571/CallGraphite'
```

After running `:PlugInstall`, restart Neovim and run `:UpdateRemotePlugins` so the Python plugin is registered.

### Using packer.nvim

```lua
use {
  'mikewong23571/CallGraphite',
  run = ':UpdateRemotePlugins'
}
```

## Usage

Open a project supported by your LSP. Then run the command:

```
:CallGraphite
```

The plugin traverses the files via LSP, extracts each function body and prints the text that would be sent to the LLM. You should see output similar to:

```
Collected 42 functions
Uploading to LLM...
```

The exact output depends on the LLM integration, but you can expect a summary once all functions are processed.

You can also capture the text of the function under the cursor using:

```
:CaptureFunction
```

This command uses tree-sitter to locate the nearest parent function and prints its source.


## Running Tests

Install the Python dependencies and run pytest:

```bash
pip install -r requirements.txt
pytest
```

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for details.
